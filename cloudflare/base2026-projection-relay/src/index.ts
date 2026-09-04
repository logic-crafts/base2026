import { handleRelayRequest } from "./relay";

export { handleRelayRequest } from "./relay";
export * from "./crypto";
export * from "./public-contract";
export * from "./relay";

export default {
  fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    return handleRelayRequest(request, env);
  },
};
