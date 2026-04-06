import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import { nanoid } from "@reduxjs/toolkit";
import { useDispatch, useSelector } from "react-redux";

import { AppDispatch, RootState } from "../../../app/store";
import { setSlides } from "../../../app/store/slices/editorSlice";
import {
  setLoading,
  setGenerating,
  setPromptSettings,
  setSlideCount as setSlideCountStore,
} from "../../../app/store/slices/promptSlice";
import { getContext } from "../../../entities";

interface ChatMessage {
  id: string;
  type: "user" | "ai";
  content: string;
  file?: File | null;
}

export const useGeneration = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState<string>("GigaChat");
  const [slideCount, setSlideCountLocal] = useState<number>(10);
  const dispatch = useDispatch<AppDispatch>();

  const { loading, slideCount: storedSlideCount } = useSelector(
    (state: RootState) => state.prompt,
  );

  const [fileStatus, setFileStatus] = useState<{
    name: string;
    converted: boolean;
  } | null>(null);

  useEffect(() => {
    setSlideCountLocal(storedSlideCount || 10);
    setMessages([
      {
        id: nanoid(),
        type: "ai",
        content:
          "Привет! Загрузи исходный файл, и я соберу структуру презентации под шаблонный экспорт.",
      },
    ]);
  }, []);

  useEffect(() => {
    setSlideCountLocal(storedSlideCount || 10);
  }, [storedSlideCount]);

  const sendMessage = async () => {
    if (!inputText.trim() || !selectedFile) {
      setError("Введите текст и прикрепите файл");
      return false;
    }

    const userMsg: ChatMessage = {
      id: nanoid(),
      type: "user",
      content: inputText,
      file: selectedFile,
    };

    setMessages((prev) => [...prev, userMsg]);
    setFileStatus({ name: selectedFile.name, converted: false });

    try {
      dispatch(setGenerating(true));
      dispatch(setLoading(true));
      dispatch(
        setPromptSettings({
          text: inputText,
          file: selectedFile,
          slideCount,
        }),
      );

      const presentation = await getContext(
        selectedFile,
        inputText,
        model,
        slideCount,
      );

      dispatch(setSlides(presentation.slides || []));
      setMessages((prev) => [
        ...prev,
        {
          id: nanoid(),
          type: "ai",
          content: `Готово: подготовлено ${presentation.slides?.length || 0} слайдов для шаблонного экспорта.`,
        },
      ]);
      setFileStatus({ name: selectedFile.name, converted: true });
      return true;
    } catch (err) {
      const detail = err instanceof Error ? err.message : "Ошибка генерации";
      setError(detail);
      return false;
    } finally {
      dispatch(setLoading(false));
      dispatch(setGenerating(false));
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setFileStatus({ name: file.name, converted: false });
  };

  const setSlideCount = (value: number) => {
    const next = Math.max(5, Math.min(20, value || 10));
    setSlideCountLocal(next);
    dispatch(setSlideCountStore(next));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    return sendMessage();
  };

  const regenerateSlides = async () => sendMessage();

  return {
    inputText,
    setInputText,
    messages,
    fileInputRef,
    fileStatus,
    handleFileChange,
    handleSubmit,
    loading,
    error,
    setError,
    model,
    setModel,
    regenerateSlides,
    slideCount,
    setSlideCount,
  };
};
