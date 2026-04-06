import React from "react";
import { Box, ToggleButton, ToggleButtonGroup } from "@mui/material";
import FormatBoldIcon from "@mui/icons-material/FormatBold";
import FormatItalicIcon from "@mui/icons-material/FormatItalic";
import CodeIcon from "@mui/icons-material/Code";
import { Editor } from "slate";
import { isMarkActive, toggleMark } from "../../lib";

interface ToolbarProps {
  editor: Editor;
}

const Toolbar: React.FC<ToolbarProps> = ({ editor }) => {
  return (
    <Box
      sx={{
        position: "absolute",
        top: -40,
        left: 50,
        zIndex: 20,
        display: "flex",
        gap: 1,
        backgroundColor: "background.paper",
        borderRadius: 1,
        boxShadow: 2,
      }}
    >
      <ToggleButtonGroup exclusive={false} size="small">
        <ToggleButton
          value="bold"
          selected={isMarkActive(editor, "bold")}
          onMouseDown={(e) => {
            e.preventDefault();
            toggleMark(editor, "bold");
          }}
        >
          <FormatBoldIcon fontSize="small" />
        </ToggleButton>

        <ToggleButton
          value="italic"
          selected={isMarkActive(editor, "italic")}
          onMouseDown={(e) => {
            e.preventDefault();
            toggleMark(editor, "italic");
          }}
        >
          <FormatItalicIcon fontSize="small" />
        </ToggleButton>

        <ToggleButton
          value="code"
          selected={isMarkActive(editor, "code")}
          onMouseDown={(e) => {
            e.preventDefault();
            toggleMark(editor, "code");
          }}
        >
          <CodeIcon fontSize="small" />
        </ToggleButton>
      </ToggleButtonGroup>
    </Box>
  );
};

export default Toolbar;
