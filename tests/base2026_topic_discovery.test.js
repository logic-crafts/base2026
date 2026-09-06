"use strict";

const assert = require("node:assert/strict");
const discovery = require("../templates/base2026-topic-discovery.js");

function recordsFixture() {
  return Array.from({ length: 50 }, (_, index) => ({
    title: index === 49 ? "Late page match & <script>" : `Topic ${String(index).padStart(2, "0")}`,
    displayTitle: index === 49 ? "Late page match & <script>" : `Topic ${String(index).padStart(2, "0")}`,
    description: index === 49 ? "A later page description" : `Description ${index}`,
    route: `/topics/topic-${index}`,
    insights: 50 - index,
    sources: index === 0 || index === 49 ? 2 : 1,
    countLabel: `${50 - index} public insights · ${index === 0 || index === 49 ? 2 : 1} sources`,
  }));
}

const records = recordsFixture();

assert.equal(discovery.canonicalRoute("/topics/valid-topic"), "/topics/valid-topic");
assert.equal(discovery.canonicalRoute("https://evil.example/topic"), "");
assert.equal(discovery.canonicalRoute("/topics/valid-topic?x=1"), "");

const laterMatch = discovery.filterRecords(records, { query: "late page match", coverage: "all", sort: "sources", page: 1 });
assert.equal(laterMatch.length, 1, "search must inspect records beyond the first pagination page");
assert.equal(laterMatch[0].route, "/topics/topic-49");

const noResults = discovery.filterRecords(records, { query: "no such topic", coverage: "all", sort: "sources", page: 1 });
assert.deepEqual(noResults, []);

const multiple = discovery.filterRecords(records, { query: "", coverage: "multiple", sort: "sources", page: 1 });
assert.equal(multiple.length, 2);
assert.ok(multiple.every((record) => record.sources > 1));

const single = discovery.filterRecords(records, { query: "", coverage: "single", sort: "sources", page: 1 });
assert.equal(single.length, 48);
assert.ok(single.every((record) => record.sources === 1));

const orderedAz = discovery.selectRecords(records, { query: "", coverage: "all", sort: "az", page: 1 });
assert.equal(orderedAz[0].displayTitle, "Late page match & <script>");
assert.equal(orderedAz[orderedAz.length - 1].displayTitle, "Topic 48");

const pageOne = discovery.paginateRecords(discovery.selectRecords(records, { sort: "sources" }), 1, 24);
const pageTwo = discovery.paginateRecords(discovery.selectRecords(records, { sort: "sources" }), 2, 24);
const pageThree = discovery.paginateRecords(discovery.selectRecords(records, { sort: "sources" }), 3, 24);
assert.deepEqual({ start: pageOne.start, end: pageOne.end, totalPages: pageOne.totalPages }, { start: 0, end: 24, totalPages: 3 });
assert.deepEqual({ start: pageTwo.start, end: pageTwo.end, items: pageTwo.items.length }, { start: 24, end: 48, items: 24 });
assert.deepEqual({ start: pageThree.start, end: pageThree.end, items: pageThree.items.length }, { start: 48, end: 50, items: 2 });
assert.match(discovery.formatRange(pageTwo), /^Showing 25–48 of 50 topics$/);
assert.equal(discovery.formatRange(discovery.paginateRecords([], 1, 24)), "No topics match these filters");

const parsed = discovery.stateFromSearch("?q=late+%3Ctag%3E&coverage=multiple&sort=az&page=2");
assert.deepEqual(parsed, { query: "late <tag>", coverage: "multiple", sort: "az", page: 2 });
const overlongQuery = "x".repeat(discovery.MAX_QUERY_LENGTH + 17);
assert.equal(discovery.stateFromSearch(`?q=${overlongQuery}`).query.length, 160);
assert.equal(discovery.normaliseState({ query: overlongQuery }).query.length, 160);

const historyCalls = [];
const fakeHistory = {
  pushState(_state, _title, path) { historyCalls.push({ method: "push", path }); },
  replaceState(_state, _title, path) { historyCalls.push({ method: "replace", path }); },
};
const fakeLocation = { pathname: "/topics/", hash: "#all" };
const pushedPath = discovery.writeUrlState(fakeLocation, fakeHistory, parsed, "push");
assert.equal(historyCalls.length, 1);
assert.equal(historyCalls[0].method, "push");
assert.equal(pushedPath, historyCalls[0].path);
assert.match(pushedPath, /^\/topics\/\?q=late\+%3Ctag%3E&coverage=multiple&sort=az&page=2#all$/);
assert.deepEqual(discovery.stateFromSearch(pushedPath.slice(pushedPath.indexOf("?"))), parsed);

discovery.writeUrlState(fakeLocation, fakeHistory, { query: "", coverage: "all", sort: "sources", page: 1 }, "replace");
assert.equal(historyCalls[1].method, "replace");

console.log("base2026 topic discovery tests passed");
