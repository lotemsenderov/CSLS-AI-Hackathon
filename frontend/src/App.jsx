// Skill 5: Styling/Layout — page shell. Owner: feature/frontend-ui branch.
import { useState } from "react";
import SearchForm from "./components/SearchForm.jsx";
import ResultsList from "./components/ResultsList.jsx";
import { searchConferences } from "./api";

export default function App() {
  const [results, setResults] = useState([]);

  async function handleSearch(field, query) {
    // TODO: setResults(await searchConferences(field, query)), handle loading/error
  }

  return (
    <div>
      <h1>Conference Finder</h1>
      <SearchForm onSearch={handleSearch} />
      <ResultsList results={results} />
    </div>
  );
}
