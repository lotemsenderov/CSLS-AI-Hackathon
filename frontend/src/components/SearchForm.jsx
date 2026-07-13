// Skill 1: Search Input Form. Owner: feature/frontend-ui branch.
// Dropdown (bound to fetchFields()) + free-text box, calls onSearch(field, query) on submit.
import { useEffect, useState } from "react";
import { fetchFields } from "../api";

export default function SearchForm({ onSearch }) {
  const [fields, setFields] = useState([]);
  const [field, setField] = useState("");
  const [query, setQuery] = useState("");

  useEffect(() => {
    // TODO: fetchFields().then(setFields)
  }, []);

  function handleSubmit(e) {
    e.preventDefault();
    // TODO: onSearch(field, query)
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* TODO: <select> bound to `fields`, <textarea> bound to `query` */}
    </form>
  );
}
