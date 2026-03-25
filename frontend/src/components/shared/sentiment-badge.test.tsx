import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SentimentBadge } from "@/components/shared/sentiment-badge";

describe("SentimentBadge", () => {
  it("renders numeric scores with sign and formatting", () => {
    render(<SentimentBadge label="positive" score={0.42} />);

    expect(screen.getByText("+0.42")).toBeInTheDocument();
  });

  it("falls back to the label when no score is provided", () => {
    render(<SentimentBadge label="very_negative" />);

    expect(screen.getByText("very negative")).toBeInTheDocument();
  });
});
