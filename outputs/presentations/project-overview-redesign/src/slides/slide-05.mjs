import { deckData } from "./project_deck_data.mjs";
import { renderSlide } from "./render_helpers.mjs";

export async function slide05(presentation, ctx) {
  return renderSlide(presentation, ctx, deckData[4], 5);
}
