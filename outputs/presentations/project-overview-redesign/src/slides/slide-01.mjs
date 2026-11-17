import { deckData } from "./project_deck_data.mjs";
import { renderSlide } from "./render_helpers.mjs";

export async function slide01(presentation, ctx) {
  return renderSlide(presentation, ctx, deckData[0], 1);
}
