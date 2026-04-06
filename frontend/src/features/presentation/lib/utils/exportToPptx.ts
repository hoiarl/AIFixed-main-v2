import { exportTemplatePresentation } from "../../../../entities/presentation/api/generateSlides";
import { PlateSlide, Theme } from "../../../../shared/types/markdownTypes";

export const exportToPptx = async (
  slides: PlateSlide[],
  _theme?: Theme,
) => {
  await exportTemplatePresentation(slides);
};
