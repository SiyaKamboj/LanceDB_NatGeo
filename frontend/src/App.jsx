import { useState } from "react";

const API_BASE_URL = "http://localhost:8000";

async function postJson(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

export default function App() {
  const [dbPath, setDbPath] = useState("");
  const [audioDir, setAudioDir] = useState("");
  const [queryAudioDir, setQueryAudioDir] = useState("");
  const [topK, setTopK] = useState(5);
  const [dbResult, setDbResult] = useState(null);
  const [audioResult, setAudioResult] = useState(null);
  const [dbLoading, setDbLoading] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [queryLoading, setQueryLoading] = useState(false);
  const [dbError, setDbError] = useState("");
  const [audioError, setAudioError] = useState("");
  const [ingestError, setIngestError] = useState("");
  const [queryError, setQueryError] = useState("");
  const [ingestResult, setIngestResult] = useState(null);
  const [queryResult, setQueryResult] = useState(null);

  const handleDbSubmit = async (event) => {
    event.preventDefault();
    setDbLoading(true);
    setDbError("");
    try {
      const result = await postJson("/api/db/init", { db_path: dbPath });
      setDbResult(result);
    } catch (err) {
      setDbError(err.message);
    } finally {
      setDbLoading(false);
    }
  };

  const handleAudioDirSubmit = async (event) => {
    event.preventDefault();
    setAudioLoading(true);
    setAudioError("");
    try {
      const result = await postJson("/api/audio-directory", { audio_dir: audioDir });
      setAudioResult(result);
    } catch (err) {
      setAudioError(err.message);
    } finally {
      setAudioLoading(false);
    }
  };

  const handleIngest = async () => {
    setIngestLoading(true);
    setIngestError("");
    try {
      const result = await postJson("/api/ingest", {
        db_path: dbPath,
        audio_dir: audioDir
      });
      setIngestResult(result);
    } catch (err) {
      setIngestError(err.message);
    } finally {
      setIngestLoading(false);
    }
  };

  const handleQuery = async (event) => {
    event.preventDefault();
    setQueryLoading(true);
    setQueryError("");
    try {
      const result = await postJson("/api/query", {
        db_path: dbPath,
        query_audio_dir: queryAudioDir,
        top_k: Number(topK)
      });
      setQueryResult(result);
    } catch (err) {
      setQueryError(err.message);
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <main className="container">
      <h1>LanceDB Audio Setup</h1>
      <p className="subtitle">Configure database and source audio paths.</p>

      <form onSubmit={handleDbSubmit} className="card">
        <h2>Database path</h2>
        <label htmlFor="dbPath">LanceDB path</label>
        <input
          id="dbPath"
          value={dbPath}
          onChange={(e) => setDbPath(e.target.value)}
          placeholder="/Users/you/Downloads/LanceDB_NatGeo/database/music_db.lance"
          required
        />
        <button type="submit" disabled={dbLoading}>
          {dbLoading ? "Connecting..." : "Connect / Create Database"}
        </button>
        {dbError ? <p className="error">{dbError}</p> : null}
      </form>

      {dbResult ? (
        <section className="card">
          <h2>Database ready</h2>
          <p>
            <strong>Path:</strong> {dbResult.db_path}
          </p>
          <p>
            <strong>Status:</strong> {dbResult.status}
          </p>
          <p>
            <strong>music_embeddings table:</strong> {dbResult.table_status}
          </p>
          <p>
            <strong>Tables:</strong> {dbResult.table_names.length ? dbResult.table_names.join(", ") : "No tables yet"}
          </p>
        </section>
      ) : null}

      <form onSubmit={handleAudioDirSubmit} className="card">
        <h2>Audio directory</h2>
        <label htmlFor="audioDir">Directory path</label>
        <input
          id="audioDir"
          value={audioDir}
          onChange={(e) => setAudioDir(e.target.value)}
          placeholder="/Users/you/Downloads/LanceDB_NatGeo/wavFiles"
          required
        />
        <button type="submit" disabled={audioLoading}>
          {audioLoading ? "Checking..." : "Validate Directory"}
        </button>
        {audioError ? <p className="error">{audioError}</p> : null}
      </form>

      {audioResult ? (
        <section className="card">
          <h2>Audio directory ready</h2>
          <p>
            <strong>Audio directory:</strong> {audioResult.audio_dir}
          </p>
          <p>
            <strong>Audio files found:</strong> {audioResult.audio_file_count}
          </p>
          {/* <p>
            <strong>Extensions:</strong> {audioResult.supported_extensions.join(", ")}
          </p> */}
          <p>Directory is validated and ready for embedding ingestion.</p>
        </section>
      ) : null}

      <section className="card">
        <h2>Generate and insert embeddings</h2>
        <p>Embeddings are generated for all recursively found audio files that are not already in LanceDB by FilePath.</p>
        <button type="button" onClick={handleIngest} disabled={ingestLoading || !dbPath || !audioDir}>
          {ingestLoading ? "Ingesting..." : "Generate + Insert"}
        </button>
        {ingestError ? <p className="error">{ingestError}</p> : null}
      </section>

      {ingestResult ? (
        <section className="card">
          <h2>Ingestion result</h2>
          <p>
            <strong>Audio files found:</strong> {ingestResult.audio_files_found}
          </p>
          <p>
            <strong>Files inserted:</strong> {ingestResult.files_inserted}
          </p>
          <p>
            <strong>Files skipped (already in DB):</strong> {ingestResult.files_skipped_existing}
          </p>
          <p>
            <strong>Embedding rows inserted:</strong> {ingestResult.embedding_rows_inserted}
          </p>
          <p>
            <strong>Failed files:</strong> {ingestResult.failed_files_count}
          </p>
        </section>
      ) : null}

      <form onSubmit={handleQuery} className="card">
        <h2>Query LanceDB</h2>
        <label htmlFor="queryAudioDir">Query audio directory path</label>
        <input
          id="queryAudioDir"
          value={queryAudioDir}
          onChange={(e) => setQueryAudioDir(e.target.value)}
          placeholder="/Users/you/Downloads/LanceDB_NatGeo/queryAudio"
          required
        />
        <label htmlFor="topK">Top K matches</label>
        <input
          id="topK"
          type="number"
          min="1"
          max="100"
          value={topK}
          onChange={(e) => setTopK(e.target.value)}
          required
        />
        <button type="submit" disabled={queryLoading || !dbPath || !queryAudioDir}>
          {queryLoading ? "Querying..." : "Run Query"}
        </button>
        {queryError ? <p className="error">{queryError}</p> : null}
      </form>

      {queryResult ? (
        <section className="card">
          <h2>Query result</h2>
          <p>
            <strong>Query files found:</strong> {queryResult.query_files_found}
          </p>
          <p>
            <strong>Top K:</strong> {queryResult.top_k}
          </p>
          <p>
            <strong>Failed files:</strong> {queryResult.failed_files_count}
          </p>
          <p>
            <strong>Rows returned:</strong> {queryResult.result_table.length}
          </p>
          {queryResult.result_table.length > 0 ? (
            <table className="resultsTable">
              <thead>
                <tr>
                  <th>Query Audio File</th>
                  <th>Query Chunk</th>
                  <th>Matched FilePaths (k)</th>
                  <th>Matched Start Seconds (k)</th>
                  <th>Matched Durations (k)</th>
                </tr>
              </thead>
              <tbody>
                {queryResult.result_table.map((row, index) => (
                  <tr key={`${row.query_file_path}-${row.query_chunk_index}-${index}`}>
                    <td>{row.query_file_path}</td>
                    <td>{row.query_chunk_index}</td>
                    <td>{row.matched_file_paths.join(", ") || "None"}</td>
                    <td>{row.matched_start_seconds.join(", ") || "None"}</td>
                    <td>{row.matched_duration_seconds.join(", ") || "None"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </section>
      ) : null}
    </main>
  );
}
