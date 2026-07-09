import { createTheme } from "@mui/material/styles";

/**
 * LaboraX theme tokens. Kept centralized so feature modules never hard-code
 * colors/typography — see docs/LLD.md §6 (frontend module layout).
 */
export const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#0F6E5B", // laboratory teal-green
      contrastText: "#FFFFFF",
    },
    secondary: {
      main: "#F2A649", // warm amber accent
    },
    error: {
      main: "#C4453A",
    },
    background: {
      default: "#F6F8F7",
      paper: "#FFFFFF",
    },
  },
  typography: {
    fontFamily: ['"Inter"', '"Segoe UI"', "Roboto", "Helvetica", "Arial", "sans-serif"].join(","),
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    button: { textTransform: "none", fontWeight: 600 },
  },
  shape: {
    borderRadius: 10,
  },
});
