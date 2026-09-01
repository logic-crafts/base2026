import { handleMemberRequest } from "./member-research";
import type { MemberAuthEnv } from "./member-auth";

export default {
  async fetch(request: Request, env: MemberAuthEnv): Promise<Response> {
    return (await handleMemberRequest(request, env)) ?? new Response("not found", { status: 404 });
  },
};
