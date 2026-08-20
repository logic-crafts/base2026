const TARGET_HOST = "base2026.dev";

export default {
  fetch(request: Request): Response {
    const target = new URL(request.url);
    target.protocol = "https:";
    target.hostname = TARGET_HOST;
    target.port = "";
    return new Response(null, {
      status: 301,
      headers: {
        Location: target.toString(),
        "Cache-Control": "public, max-age=3600",
      },
    });
  },
} satisfies ExportedHandler;
