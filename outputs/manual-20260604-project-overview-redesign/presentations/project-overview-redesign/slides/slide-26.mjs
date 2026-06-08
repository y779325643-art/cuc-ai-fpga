import { deckData } from "./project_deck_data.mjs";
import { renderSlide } from "./render_helpers.mjs";

export async function slide26(presentation, ctx) {
  return renderSlide(presentation, ctx, deckData[25], 26);
}
