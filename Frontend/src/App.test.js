import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders app title", () => {
  render(<App />);
  const titleElement = screen.getByText(/AI-BI: Business Intelligence with AI/i);
  expect(titleElement).toBeInTheDocument();
});