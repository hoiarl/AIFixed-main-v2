import React from "react";
import { Box, Button } from "@mui/material";
import { useNavigate, useLocation } from "react-router-dom";

const HeaderAuthBlock: React.FC<{ isMobile?: boolean }> = ({ isMobile }) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
      {location.pathname !== "/projects" && (
        <Button
          variant="outlined"
          sx={{ textTransform: "none" }}
          onClick={() => navigate("/projects")}
        >
          {isMobile ? "Проекты" : "Мои презентации"}
        </Button>
      )}
      {location.pathname !== "/" && (
        <Button
          variant="contained"
          sx={{ textTransform: "none" }}
          onClick={() => navigate("/")}
        >
          {isMobile ? "Главная" : "Новая презентация"}
        </Button>
      )}
    </Box>
  );
};

export default HeaderAuthBlock;
