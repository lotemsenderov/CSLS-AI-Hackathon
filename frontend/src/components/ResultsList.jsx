// Skills 2-3: Results Display + Filter & Sort Controls. Owner: feature/frontend-ui branch.
// Renders `results` (already ranked by score from the backend) with
// client-side sort/filter by date and location.
import { useState } from "react";

export default function ResultsList({ results }) {
  const [sortBy, setSortBy] = useState("score");
  const [locationFilter, setLocationFilter] = useState("");

  // TODO: derive a sorted/filtered view of `results` from sortBy + locationFilter

  return (
    <div>
      {/* TODO: sort/filter controls, then map over results rendering a card per conference */}
    </div>
  );
}
