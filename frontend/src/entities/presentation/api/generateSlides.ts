import { PlateSlide } from "../../../shared/types";

export interface GeneratedPresentationPayload {
  slides: PlateSlide[];
  templateMode?: string;
  templateRequired?: boolean;
  exportEngine?: string;
}

export const getContext = async (
  file: File,
  text: string,
  model: string,
  slideCount: number,
): Promise<GeneratedPresentationPayload> => {
  const formData = new FormData();
  formData.append("text", text);
  formData.append("file", file);
  formData.append("model", model);
  formData.append("slide_count", String(slideCount));

  const resp = await fetch(
    `${process.env.REACT_APP_API_URL}/presentation/generate-json`,
    {
      method: "POST",
      body: formData,
    },
  );

  if (!resp.ok) {
    let detail = "Ошибка генерации презентации";
    try {
      const data = await resp.json();
      detail = data?.detail || detail;
    } catch {
      // no-op
    }
    throw new Error(detail);
  }

  return resp.json();
};

export const exportTemplatePresentation = async (slides: PlateSlide[]) => {
  const resp = await fetch(
    `${process.env.REACT_APP_API_URL}/presentation/export-template`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ slides }),
    },
  );

  if (!resp.ok) {
    let detail = "Ошибка экспорта PPTX";
    try {
      const data = await resp.json();
      detail = data?.detail || detail;
    } catch {
      // no-op
    }
    throw new Error(detail);
  }

  const blob = await resp.blob();
  const disposition = resp.headers.get("Content-Disposition") || "";
  const fileNameMatch = disposition.match(/filename="?([^\"]+)"?/i);
  const fileName = fileNameMatch?.[1] || "presentation-template.pptx";

  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
