import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { create } from "domain";

interface PromptStateProps {
  file: File | null;
  text: string;
  slideCount: number;
  loading: boolean;
  generating: boolean;
}

const initialState: PromptStateProps = {
  file: null,
  text: "",
  slideCount: 10,
  loading: false,
  generating: false,
};

const promptSlice = createSlice({
  name: "prompt",
  initialState,
  reducers: {
    setPromptSettings: (
      state,
      action: PayloadAction<{
        file: File | null;
        text: string;
        slideCount?: number;
      }>,
    ) => {
      const { text, file, slideCount } = action.payload;
      state.text = text;
      state.file = file || null;
      if (typeof slideCount === "number") state.slideCount = slideCount;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setGenerating: (state, action: PayloadAction<boolean>) => {
      state.generating = action.payload;
    },
    setSlideCount: (state, action: PayloadAction<number>) => {
      state.slideCount = action.payload;
    },
  },
});

export const { setPromptSettings, setLoading, setGenerating, setSlideCount } =
  promptSlice.actions;
export default promptSlice.reducer;
