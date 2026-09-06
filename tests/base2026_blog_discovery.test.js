const test = require('node:test');
const assert = require('node:assert/strict');
const discovery = require('../templates/base2026-blog-discovery.js');

function article(id, overrides = {}) {
  return {
    id, path: `/blog/${id}/`, title: `Research ${id}`, description: 'A useful public research method.',
    category: 'Research methods', author: 'Alex Yarosh', published_at: '2026-09-01T12:00:00.000Z',
    updated_at: '2026-09-01T12:00:00.000Z', ...overrides
  };
}

function page(articles, cursor = null) {
  return { schema_version: 'base2026.editorial-index.v1', articles, next_cursor: cursor,
    next_url: cursor ? '/blog?cursor=' + encodeURIComponent(cursor.published_at + '|' + cursor.slug) : null };
}

function response(payload) { return { ok: true, json: async () => payload }; }

test('search includes later cursor pages and categories use the complete index', async () => {
  const cursor = { published_at: '2026-09-01T12:00:00.000Z', slug: 'first-page-last' };
  const first = Array.from({ length: 25 }, (_, i) => article('first-' + i));
  const later = article('later-match', { title: 'Measuring crawler behaviour', category: 'Engineering', published_at: '2026-08-29' });
  const calls = [];
  const all = await discovery.loadAllArticles(async (url, options) => {
    calls.push({ url, options });
    return response(calls.length === 1 ? page(first, cursor) : page([later]));
  });
  assert.equal(calls.length, 2);
  assert.equal(calls[0].url, '/api/blog');
  assert.equal(calls[1].url, '/api/blog?cursor=' + encodeURIComponent(cursor.published_at + '|' + cursor.slug));
  assert.ok(calls.every(call => call.options.method === 'GET' && call.options.credentials === 'omit'));
  assert.equal(all.length, 26);
  assert.deepEqual(discovery.categoriesFor(all), [['Engineering', 1], ['Research methods', 25]]);
  assert.deepEqual(discovery.selectArticles(all, { q: 'crawler measuring', category: 'Engineering', page: 1 }).items.map(item => item.path), ['/blog/later-match/']);
});

test('a failed continuation never returns a partial searchable index', async () => {
  const cursor = { published_at: '2026-09-01T12:00:00.000Z', slug: 'next' };
  let calls = 0;
  await assert.rejects(discovery.loadAllArticles(async () => ++calls === 1 ? response(page([article('one')], cursor)) : { ok: false }), /UNAVAILABLE/);
  assert.equal(calls, 2);
});

test('cursor loops and inconsistent terminal cursors are rejected', async () => {
  const cursor = { published_at: '2026-09-01T12:00:00.000Z', slug: 'same' };
  let calls = 0;
  await assert.rejects(discovery.loadAllArticles(async () => { calls++; return response(page([article('one')], cursor)); }), /INCOMPLETE/);
  assert.equal(calls, 2);
  assert.throws(() => discovery.nextApiPath(null, cursor), /CURSOR_INVALID/);
});

test('pagination links cannot send requests to a foreign origin or private route', () => {
  const cursor = { published_at: '2026-09-01T12:00:00.000Z', slug: 'one' };
  const query = '?cursor=' + encodeURIComponent(cursor.published_at + '|' + cursor.slug);
  for (const url of ['https://other.example/blog' + query, '/api/my-research' + query, '/blog' + query + '&secret=x', '/blog' + query + '#section']) {
    assert.throws(() => discovery.nextApiPath(url, cursor), /CURSOR_INVALID/);
  }
  assert.equal(discovery.nextApiPath('/blog' + query, cursor), '/api/blog' + query);
});

test('deduplication preserves the first canonical record and date order', async () => {
  const original = article('one');
  const all = await discovery.loadAllArticles(async () => response(page([original, { ...original, title: 'duplicate' }, article('newer', { published_at: '2026-09-06' })])));
  assert.deepEqual(all.map(item => item.id), ['newer', 'one']);
  assert.equal(all[1].title, original.title);
});

test('empty, filtered, and out-of-range pages retain correct totals', () => {
  const articles = Array.from({ length: 20 }, (_, i) => article('note-' + i));
  const last = discovery.selectArticles(articles, { q: '', category: '', page: 999 });
  assert.equal(last.page, 3); assert.equal(last.pages, 3); assert.equal(last.total, 20); assert.equal(last.items.length, 2);
  const empty = discovery.selectArticles(articles, { q: 'no-such-topic', category: '', page: 8 });
  assert.equal(empty.page, 1); assert.equal(empty.total, 0); assert.deepEqual(empty.items, []);
  assert.equal(discovery.selectArticles(articles, { q: 'research', category: 'Engineering', page: 1 }).total, 0);
});

test('query/category/page survive shared URLs and back-forward state parsing', () => {
  const initial = 'https://base2026.dev/blog?cursor=old&from=directory';
  const searched = discovery.stateUrl({ q: 'source methods', category: 'Research methods', page: 2 }, initial);
  assert.equal(searched, '/blog?from=directory&q=source+methods&category=Research+methods&page=2');
  assert.deepEqual(discovery.readState(searched), { q: 'source methods', category: 'Research methods', page: 2 });
  const cleared = discovery.stateUrl({ q: '', category: '', page: 1 }, searched);
  assert.equal(cleared, '/blog?from=directory');
  assert.deepEqual(discovery.readState(searched), { q: 'source methods', category: 'Research methods', page: 2 });
  assert.equal(discovery.readState('/blog?page=-2').page, 1);
});

test('API text remains text and only canonical article/image paths are admitted', () => {
  const input = article('safe', { title: '<img src=x onerror=alert(1)>', category: 'A & B' });
  assert.equal(discovery.normalizeArticle(input).title, input.title);
  assert.throws(() => discovery.normalizeArticle(article('unsafe', { path: 'javascript:alert(1)' })), /INVALID/);
  assert.throws(() => discovery.normalizeArticle(article('unsafe', { hero: { path: 'https://other.example/image.png', alt: 'Image', credit: 'Creator' } })), /IMAGE_INVALID/);
  assert.throws(() => discovery.normalizeArticle(article('unsafe', { path: '/blog/../my-research/' })), /INVALID/);
  const state = discovery.readState('/blog?q=%3Cscript%3E&category=A+%26+B');
  assert.equal(state.q, '<script>');
  assert.ok(discovery.stateUrl(state, '/blog').includes('%3Cscript%3E'));
});
