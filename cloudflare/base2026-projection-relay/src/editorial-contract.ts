/**
 * Editorial validation is public-safe and remains owned by the target public
 * Worker. The relay uses it only as a pre-forward privacy/shape gate; it does
 * not normalize or author the packet before the RPC call.
 */
export {
  EDITORIAL_EVIDENCE_GUIDE_SLUGS,
  validateEditorialPacket,
  validateEditorialPayload,
} from "../../base2026-worker/src/editorial";

export type {
  EditorialPacket,
  EditorialPacketValidation,
  EditorialPayload,
  EditorialPublishResult,
  EditorialReview,
  EditorialOverwrite,
} from "../../base2026-worker/src/editorial";
