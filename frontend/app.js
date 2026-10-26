const API = "";


// ============================================================
// STATE
// ============================================================

const state = {
  documents: [],
  selectedDocumentIds: new Set(),
  mode: "explore"
};


// ============================================================
// ELEMENTS
// ============================================================

const paperList = document.getElementById("paper-list");
const paperCount = document.getElementById("paper-count");

const paperSearch = document.getElementById("paper-search");
const paperFilterInput = document.getElementById("paper-filter-input");

const pdfInput = document.getElementById("pdf-input");
const dropZone = document.getElementById("drop-zone");
const uploadStatus = document.getElementById("upload-status");

const refreshDocsButton = document.getElementById("refresh-docs");

const queryInput = document.getElementById("query-input");
const topKSelect = document.getElementById("top-k");
const topKLabel = document.getElementById("top-k-label");

const runButton = document.getElementById("run-btn");
const runLabel = document.getElementById("run-label");

const analysisTitle = document.getElementById("analysis-title");
const analysisSubtitle = document.getElementById("analysis-subtitle");

const selectionHint = document.getElementById("selection-hint");
const scopeControl = document.getElementById("scope-control");

const resultShell = document.getElementById("result-shell");
const singleResultShell = document.getElementById("single-result-shell");

const summaryContent = document.getElementById("summary-content");
const byDocumentContent = document.getElementById("by-document-content");
const differencesContent = document.getElementById("differences-content");
const evidenceChips = document.getElementById("evidence-chips");

const singleResultTitle = document.getElementById("single-result-title");
const singleResultMain = document.getElementById("single-result-main");
const singleResultMeta = document.getElementById("single-result-meta");
const singleEvidenceList = document.getElementById("single-evidence-list");

const globalStatus = document.getElementById("global-status");

function getOrCreateSessionId() {
  let sessionId =
    localStorage.getItem("litlens_session_id");

  if (!sessionId) {
    sessionId = crypto.randomUUID();

    localStorage.setItem(
      "litlens_session_id",
      sessionId
    );
  }

  return sessionId;
}


const sessionId = getOrCreateSessionId();

console.log(
  "LitLens session ID:",
  sessionId
);


// 下面继续你原来的 app.js 代码


// ============================================================
// HELPERS
// ============================================================

function escapeHtml(value) {
  if (value === null || value === undefined) {
    return "";
  }

  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function showStatus(message, type = "info") {
  globalStatus.textContent = message;
  globalStatus.classList.remove("hidden");
  globalStatus.dataset.type = type;
}


function hideStatus() {
  globalStatus.classList.add("hidden");
  globalStatus.textContent = "";
}


function setLoading(isLoading) {
  runButton.disabled = isLoading;

  if (isLoading) {
    runLabel.textContent = "Working...";
  } else {
    updateRunButtonLabel();
  }
}


function updateRunButtonLabel() {
  if (state.mode === "ask") {
    runLabel.textContent = "Ask LitLens";
  } else if (state.mode === "verify") {
    runLabel.textContent = "Verify Claim";
  } else {
    runLabel.textContent = "Run Analysis";
  }
}


function getSelectedDocumentIds() {
  return [...state.selectedDocumentIds];
}


function getSearchScope() {
  const checked = document.querySelector(
    'input[name="search-scope"]:checked'
  );

  return checked ? checked.value : "all";
}


function getDocumentName(documentId) {
  const item = state.documents.find(
    (documentItem) =>
      documentItem.document_id === documentId
  );

  if (!item) {
    return `Document ${documentId}`;
  }

  return item.title || item.filename;
}


function paperSelectionEnabled() {
  if (state.mode === "explore") {
    return true;
  }

  return getSearchScope() === "selected";
}


// ============================================================
// DOCUMENTS
// ============================================================

async function loadDocuments() {
  try {
    const response = await fetch(
      `${API}/documents`,
      {
        headers: {
          "X-Session-ID": sessionId
        }
      }
    );

    if (!response.ok) {
      throw new Error("Could not load documents.");
    }

    state.documents = await response.json();

    const validIds = new Set(
      state.documents.map(
        (item) => item.document_id
      )
    );

    state.selectedDocumentIds = new Set(
      [...state.selectedDocumentIds].filter(
        (id) => validIds.has(id)
      )
    );

    renderDocuments();

  } catch (error) {

    paperList.innerHTML = `
      <div class="empty-state">
        Could not load documents.
      </div>
    `;

    showStatus(
      error.message,
      "error"
    );
  }
}


function renderDocuments() {
  const searchValue =
    (
      paperFilterInput?.value ||
      paperSearch?.value ||
      ""
    )
      .trim()
      .toLowerCase();


  const enabled =
    paperSelectionEnabled();


  const filteredDocuments =
    state.documents.filter(
      (documentItem) => {

        const filename =
          (
            documentItem.filename || ""
          ).toLowerCase();

        const title =
          (
            documentItem.title || ""
          ).toLowerCase();

        return (
          filename.includes(searchValue) ||
          title.includes(searchValue)
        );
      }
    );


  paperCount.textContent =
    state.documents.length;


  if (filteredDocuments.length === 0) {

    paperList.innerHTML = `
      <div class="empty-state">
        No papers found.
      </div>
    `;

    return;
  }


  paperList.innerHTML =
    filteredDocuments
      .map((documentItem) => {

        const documentId =
          documentItem.document_id;


        const checked =
          state.selectedDocumentIds.has(
            documentId
          )
            ? "checked"
            : "";


        const disabled =
          enabled
            ? ""
            : "disabled";


        const disabledClass =
          enabled
            ? ""
            : "selection-disabled";


        const title =
          documentItem.title &&
          documentItem.title !==
            documentItem.filename
            ? documentItem.title
            : documentItem.filename;


        const subtitle =
          documentItem.title &&
          documentItem.title !==
            documentItem.filename
            ? documentItem.filename
            : "";

        return `
          <div class="paper-row">

            <label class="paper-item${disabledClass}">

              <input
                type="checkbox"
                class="paper-checkbox"
                data-document-id="${documentId}"
                ${checked}
                ${disabled}
              />

              <div class="paper-item-text">

                <div class="paper-item-title">
                  ${escapeHtml(title)}
                </div>

                ${
                  subtitle
                    ? `
                      <div class="paper-item-subtitle">
                        ${escapeHtml(subtitle)}
                      </div>
                    `
                    : ""
                }

              </div>

            </label>

            <button
              type="button"
              class="paper-remove-button"
              data-document-id="${documentId}"
            >
              Remove
            </button>

          </div>
        `;

        
      })
      .join("");


  paperList
    .querySelectorAll(".paper-checkbox")
    .forEach((checkbox) => {

      checkbox.addEventListener(
        "change",
        () => {

          const documentId =
            Number(
              checkbox.dataset.documentId
            );


          if (checkbox.checked) {

            state.selectedDocumentIds.add(
              documentId
            );

          } else {

            state.selectedDocumentIds.delete(
              documentId
            );
          }


          updateSelectionHint();
        }
      );
        });


  paperList
    .querySelectorAll(".paper-remove-button")
    .forEach((button) => {

      button.addEventListener(
        "click",
        async () => {

          const documentId =
            Number(
              button.dataset.documentId
            );

          const confirmed =
            window.confirm(
              "Remove this paper from your workspace?"
            );

          if (!confirmed) {
            return;
          }

          try {

            const response =
              await fetch(
                `/documents/${documentId}`,
                {
                  method: "DELETE",
                  headers: {
                    "X-Session-ID": sessionId
                  }
                }
              );

            if (!response.ok) {

              const errorData =
                await response.json();

              throw new Error(
                errorData.detail ||
                "Could not remove paper."
              );
            }

            state.selectedDocumentIds.delete(
              documentId
            );

            await loadDocuments();

            showStatus(
              "Paper removed.",
              "success"
            );

          } catch (error) {

            showStatus(
              error.message,
              "error"
            );
          }
        }
      );
    });


  updateSelectionHint();
}


function updateSelectionHint() {
  const count =
    state.selectedDocumentIds.size;


  if (state.mode !== "explore") {
    return;
  }


  if (count < 2) {

    selectionHint.textContent =
      `Select at least two papers on the left for Explore. ${count} selected.`;

  } else {

    selectionHint.textContent =
      `${count} papers selected for comparison.`;
  }
}


// ============================================================
// UPLOAD
// ============================================================

async function uploadPdf(file) {
  if (!file) {
    return;
  }


  if (
    file.type !== "application/pdf" &&
    !file.name
      .toLowerCase()
      .endsWith(".pdf")
  ) {

    uploadStatus.textContent =
      "Please choose a PDF file.";

    return;
  }


  const formData =
    new FormData();


  formData.append(
    "file",
    file
  );


  uploadStatus.textContent =
    "Uploading and processing PDF...";


  try {

    const response = await fetch(
  `${API}/documents/upload`,
  {
    method: "POST",

    headers: {
      "X-Session-ID": sessionId
    },

    body: formData
  }
);


    const data =
      await response.json();


    if (!response.ok) {

      throw new Error(
        data.detail ||
        "Upload failed."
      );
    }


    uploadStatus.textContent =
      "PDF uploaded successfully.";


    await loadDocuments();

  } catch (error) {

    uploadStatus.textContent =
      error.message;
  }
}


// ============================================================
// MODE SWITCHING
// ============================================================

function setMode(mode) {

  state.mode = mode;


  hideStatus();


  resultShell.classList.add(
    "hidden"
  );

  singleResultShell.classList.add(
    "hidden"
  );


  document
    .querySelectorAll("[data-mode]")
    .forEach((button) => {

      button.classList.toggle(
        "active",
        button.dataset.mode === mode
      );
    });


  // --------------------------------------------------------
  // ASK
  // --------------------------------------------------------

  if (mode === "ask") {

    analysisTitle.textContent =
      "Ask Your Papers";


    analysisSubtitle.textContent =
      "Ask a question and receive an evidence-grounded answer.";


    // No example sentence inside the box
    queryInput.placeholder = "";


    topKLabel.textContent =
      "Top evidence";


    selectionHint.classList.add(
      "hidden"
    );


    scopeControl.classList.remove(
      "hidden"
    );


  // --------------------------------------------------------
  // VERIFY
  // --------------------------------------------------------

  } else if (mode === "verify") {

    analysisTitle.textContent =
      "Verify a Claim";


    analysisSubtitle.textContent =
      "Check whether your papers support, contradict, or do not contain enough evidence for a claim.";


    // No example sentence inside the box
    queryInput.placeholder = "";


    topKLabel.textContent =
      "Top evidence";


    selectionHint.classList.add(
      "hidden"
    );


    scopeControl.classList.remove(
      "hidden"
    );


  // --------------------------------------------------------
  // EXPLORE
  // --------------------------------------------------------

  } else {

    analysisTitle.textContent =
      "Explore Your Papers";


    analysisSubtitle.textContent =
      "Ask comparative questions and discover how papers agree or differ.";


    // No example sentence inside the box
    queryInput.placeholder = "";


    topKLabel.textContent =
      "Evidence per paper";


    scopeControl.classList.add(
      "hidden"
    );


    selectionHint.classList.remove(
      "hidden"
    );


    updateSelectionHint();
  }


  updateRunButtonLabel();


  // Refresh paper checkboxes:
  //
  // Ask/Verify + All papers
  // → disabled
  //
  // Ask/Verify + Selected papers
  // → enabled
  //
  // Explore
  // → enabled

  renderDocuments();
}


// ============================================================
// ASK
// ============================================================

async function runAsk() {

  const question =
    queryInput.value.trim();


  if (!question) {

    showStatus(
      "Please enter a question.",
      "error"
    );

    return;
  }


  const scope =
    getSearchScope();


  let documentIds = null;


  if (scope === "selected") {

    documentIds =
      getSelectedDocumentIds();


    if (documentIds.length === 0) {

      showStatus(
        "Select at least one paper, or switch Search scope to All papers.",
        "error"
      );

      return;
    }
  }


  const payload = {

    question: question,

    top_k:
      Number(
        topKSelect.value
      ),

    document_ids:
      documentIds
  };


  setLoading(true);

  hideStatus();


  try {

    const response = await fetch(
      `${API}/ask`,
      {
        method: "POST",

        headers: {
        "Content-Type": "application/json",
        "X-Session-ID": sessionId
      },

        body:
          JSON.stringify(
            payload
          )
      }
    );


    const data =
      await response.json();


    if (!response.ok) {

      throw new Error(
        data.detail ||
        "Ask request failed."
      );
    }


    renderAskResult(
      data
    );

  } catch (error) {

    showStatus(
      error.message,
      "error"
    );

  } finally {

    setLoading(false);
  }
}


function renderAskResult(data) {

  resultShell.classList.add(
    "hidden"
  );


  singleResultShell.classList.remove(
    "hidden"
  );


  const evidenceIds =
    data.evidence_ids || [];


  const evidenceCandidates =
    data.evidence || [];


  singleResultTitle.textContent =
    evidenceIds.length === 0
      ? "Insufficient Evidence"
      : "Answer";


  singleResultMain.innerHTML = `
    <div class="prose">

      ${escapeHtml(
        data.answer ||
        "No answer returned."
      )}

    </div>
  `;


  const scope =
    getSearchScope();


  if (scope === "selected") {

    const selectedNames =
      getSelectedDocumentIds()
        .map(
          getDocumentName
        )
        .join(", ");


    singleResultMeta.innerHTML = `
      <span>
        Search scope:
        <strong>
          ${escapeHtml(
            selectedNames
          )}
        </strong>
      </span>
    `;

  } else {

    singleResultMeta.innerHTML = `
      <span>
        Search scope:
        <strong>
          All papers
        </strong>
      </span>
    `;
  }


  // Retriever always returns candidates.
  // Only IDs returned by the LLM are true supporting evidence.

  if (evidenceIds.length === 0) {

    singleEvidenceList.innerHTML = `
      <div class="empty-state">
        No supporting evidence was found in the current search scope.
      </div>
    `;

    return;
  }


  const supportingEvidence =
    evidenceCandidates.filter(
      (item) =>
        evidenceIds.includes(
          item.evidence_id
        )
    );


  if (
    supportingEvidence.length === 0
  ) {

    singleEvidenceList.innerHTML =
      evidenceIds
        .map(
          (evidenceId) => `
            <div class="evidence-item">

              <strong>
                ${escapeHtml(
                  evidenceId
                )}
              </strong>

            </div>
          `
        )
        .join("");

    return;
  }


  singleEvidenceList.innerHTML =
    supportingEvidence
      .map(
        (item) => `
          <div class="evidence-item">

            <div class="evidence-item-header">

              <strong>
                ${escapeHtml(
                  item.filename
                )}
              </strong>

              <span>
                Page ${item.page_number}
              </span>

            </div>

            <div class="evidence-id">
              ${escapeHtml(
                item.evidence_id
              )}
            </div>

            <p>
              ${escapeHtml(
                item.text
              )}
            </p>

          </div>
        `
      )
      .join("");
}


// ============================================================
// VERIFY
// ============================================================

async function runVerify() {

  const claim =
    queryInput.value.trim();


  if (!claim) {

    showStatus(
      "Please enter a claim.",
      "error"
    );

    return;
  }


  const scope =
    getSearchScope();


  let documentIds = null;


  if (scope === "selected") {

    documentIds =
      getSelectedDocumentIds();


    if (documentIds.length === 0) {

      showStatus(
        "Select at least one paper, or switch Search scope to All papers.",
        "error"
      );

      return;
    }
  }


  const payload = {

    claim: claim,

    top_k:
      Number(
        topKSelect.value
      ),

    document_ids:
      documentIds
  };


  setLoading(true);

  hideStatus();


  try {

    const response = await fetch(
      `${API}/verify`,
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": sessionId
        },

        body:
          JSON.stringify(
            payload
          )
      }
    );


    const data =
      await response.json();


    if (!response.ok) {

      throw new Error(
        data.detail ||
        "Verify request failed."
      );
    }


    renderVerifyResult(
      data
    );

  } catch (error) {

    showStatus(
      error.message,
      "error"
    );

  } finally {

    setLoading(false);
  }
}


function renderVerifyResult(data) {

  resultShell.classList.add(
    "hidden"
  );


  singleResultShell.classList.remove(
    "hidden"
  );


  const evidenceIds =
    data.evidence_ids || [];


  const evidenceCandidates =
    data.evidence || [];


  singleResultTitle.textContent =
    "Verification";


  singleResultMain.innerHTML = `
    <div class="verification-result">

      <div class="verification-verdict">

        ${escapeHtml(
          data.verdict ||
          "UNKNOWN"
        )}

      </div>

      ${
        data.confidence !== undefined
          ? `
            <div class="verification-confidence">

              Confidence:
              ${escapeHtml(
                data.confidence
              )}

            </div>
          `
          : ""
      }

      <div class="prose">

        ${escapeHtml(
          data.reasoning || ""
        )}

      </div>

    </div>
  `;


  const scope =
    getSearchScope();


  if (scope === "selected") {

    const selectedNames =
      getSelectedDocumentIds()
        .map(
          getDocumentName
        )
        .join(", ");


    singleResultMeta.innerHTML = `
      <span>

        Search scope:

        <strong>
          ${escapeHtml(
            selectedNames
          )}
        </strong>

      </span>
    `;

  } else {

    singleResultMeta.innerHTML = `
      <span>

        Search scope:

        <strong>
          All papers
        </strong>

      </span>
    `;
  }


  if (evidenceIds.length === 0) {

    singleEvidenceList.innerHTML = `
      <div class="empty-state">

        No supporting evidence was used for this verification.

      </div>
    `;

    return;
  }


  const supportingEvidence =
    evidenceCandidates.filter(
      (item) =>
        evidenceIds.includes(
          item.evidence_id
        )
    );


  if (
    supportingEvidence.length === 0
  ) {

    singleEvidenceList.innerHTML =
      evidenceIds
        .map(
          (evidenceId) => `
            <div class="evidence-item">

              <strong>
                ${escapeHtml(
                  evidenceId
                )}
              </strong>

            </div>
          `
        )
        .join("");

    return;
  }


  singleEvidenceList.innerHTML =
    supportingEvidence
      .map(
        (item) => `
          <div class="evidence-item">

            <div class="evidence-item-header">

              <strong>
                ${escapeHtml(
                  item.filename
                )}
              </strong>

              <span>
                Page ${item.page_number}
              </span>

            </div>

            <div class="evidence-id">

              ${escapeHtml(
                item.evidence_id
              )}

            </div>

            <p>

              ${escapeHtml(
                item.text
              )}

            </p>

          </div>
        `
      )
      .join("");
}


// ============================================================
// EXPLORE
// ============================================================

async function runExplore() {

  const question =
    queryInput.value.trim();


  if (!question) {

    showStatus(
      "Please enter a comparison question.",
      "error"
    );

    return;
  }


  const documentIds =
    getSelectedDocumentIds();


  if (documentIds.length < 2) {

    showStatus(
      "Explore requires at least two selected papers.",
      "error"
    );

    return;
  }


  const payload = {

    question:
      question,

    document_ids:
      documentIds,

    top_k_per_document:
      Number(
        topKSelect.value
      )
  };


  setLoading(true);

  hideStatus();


  try {

    const response = await fetch(
      `${API}/explore`,
      {
        method:
          "POST",

        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": sessionId
        },
        body:
          JSON.stringify(
            payload
          )
      }
    );


    const data =
      await response.json();


    if (!response.ok) {

      throw new Error(
        data.detail ||
        "Explore request failed."
      );
    }


    renderExploreResult(
      data
    );

  } catch (error) {

    showStatus(
      error.message,
      "error"
    );

  } finally {

    setLoading(false);
  }
}


function renderExploreResult(data) {
  singleResultShell.classList.add(
    "hidden"
  );


  resultShell.classList.remove(
    "hidden"
  );


  summaryContent.innerHTML = `
    <p>

      ${escapeHtml(
        data.summary ||
        "No summary returned."
      )}

    </p>
  `;


  const byDocument =
    data.by_document || [];


  byDocumentContent.innerHTML =
    byDocument.length > 0
      ? byDocument
          .map(
            (item) => {

              const status =
                item.status ||
                "UNKNOWN";


              return `
                <div class="document-finding">

                  <div class="document-finding-header">

                    <strong>

                      ${escapeHtml(
                        item.filename ||
                        getDocumentName(
                          item.document_id
                        )
                      )}

                    </strong>

                    <span class="status-badge">

                      ${escapeHtml(
                        status
                      )}

                    </span>

                  </div>

                  <p>

                    ${escapeHtml(
                      item.finding ||
                      item.summary ||
                      ""
                    )}

                  </p>

                  ${
                    item.evidence_ids &&
                    item.evidence_ids.length > 0
                      ? `
                        <div class="evidence-chips">

                          ${item.evidence_ids
                            .map(
                              (id) => `
                                <span class="evidence-chip">

                                  ${escapeHtml(
                                    id
                                  )}

                                </span>
                              `
                            )
                            .join("")}

                        </div>
                      `
                      : `
                        <div class="helper-text">

                          No supporting evidence used.

                        </div>
                      `
                  }

                </div>
              `;
            }
          )
          .join("")
      : `
        <div class="empty-state">

          No document-level findings returned.

        </div>
      `;


  const agreements =
    data.agreements || [];


  const differences =
    data.differences || [];


  let differencesHtml = "";


  if (agreements.length > 0) {

    differencesHtml += `
      <div class="comparison-block">

        <h4>
          Agreements
        </h4>

        <ul>

          ${agreements
            .map(
              (item) => `
                <li>

                  ${escapeHtml(
                    item
                  )}

                </li>
              `
            )
            .join("")}

        </ul>

      </div>
    `;
  }


  if (differences.length > 0) {

    differencesHtml += `
      <div class="comparison-block">

       

        <ul>

          ${differences
            .map(
              (item) => `
                <li>

                  ${escapeHtml(
                    item
                  )}

                </li>
              `
            )
            .join("")}

        </ul>

      </div>
    `;
  }


  if (!differencesHtml) {

    differencesHtml = `
      <div class="empty-state">

        No meaningful agreements or differences were identified.

      </div>
    `;
  }


  differencesContent.innerHTML =
    differencesHtml;


  const evidenceIds =
    data.evidence_ids || [];


  if (evidenceIds.length === 0) {

    evidenceChips.innerHTML = `
      <span class="helper-text">

        No supporting evidence was used.

      </span>
    `;

  } else {

    evidenceChips.innerHTML =
      evidenceIds
        .map(
          (id) => `
            <span class="evidence-chip">

              ${escapeHtml(
                id
              )}

            </span>
          `
        )
        .join("");
  }


  activateResultPanel(
    "summary-panel"
  );
}


// ============================================================
// RUN BUTTON
// ============================================================

async function runCurrentMode() {

  if (state.mode === "ask") {

    await runAsk();

  } else if (
    state.mode === "verify"
  ) {

    await runVerify();

  } else {

    await runExplore();
  }
}


// ============================================================
// RESULT TABS
// ============================================================

function activateResultPanel(panelId) {

  document
    .querySelectorAll(
      ".result-panel"
    )
    .forEach(
      (panel) => {

        panel.classList.toggle(
          "active",
          panel.id === panelId
        );
      }
    );


  document
    .querySelectorAll(
      ".result-tab"
    )
    .forEach(
      (tab) => {

        tab.classList.toggle(
          "active",
          tab.dataset.resultPanel ===
            panelId
        );
      }
    );
}


// ============================================================
// EVENT LISTENERS
// ============================================================

runButton.addEventListener(
  "click",
  runCurrentMode
);


refreshDocsButton.addEventListener(
  "click",
  loadDocuments
);


paperFilterInput.addEventListener(
  "input",
  renderDocuments
);


paperSearch.addEventListener(
  "input",
  () => {

    paperFilterInput.value =
      paperSearch.value;


    renderDocuments();
  }
);


pdfInput.addEventListener(
  "change",
  () => {

    const file =
      pdfInput.files[0];


    uploadPdf(
      file
    );


    pdfInput.value = "";
  }
);


dropZone.addEventListener(
  "dragover",
  (event) => {

    event.preventDefault();


    dropZone.classList.add(
      "dragging"
    );
  }
);


dropZone.addEventListener(
  "dragleave",
  () => {

    dropZone.classList.remove(
      "dragging"
    );
  }
);


dropZone.addEventListener(
  "drop",
  (event) => {

    event.preventDefault();


    dropZone.classList.remove(
      "dragging"
    );


    const file =
      event.dataTransfer.files[0];


    uploadPdf(
      file
    );
  }
);


document
  .querySelectorAll(
    "[data-mode]"
  )
  .forEach(
    (button) => {

      button.addEventListener(
        "click",
        () => {

          setMode(
            button.dataset.mode
          );
        }
      );
    }
  );


document
  .querySelectorAll(
    ".result-tab"
  )
  .forEach(
    (tab) => {

      tab.addEventListener(
        "click",
        () => {

          activateResultPanel(
            tab.dataset.resultPanel
          );
        }
      );
    }
  );


document
  .querySelectorAll(
    'input[name="search-scope"]'
  )
  .forEach(
    (radio) => {

      radio.addEventListener(
        "change",
        () => {

          renderDocuments();

          hideStatus();
        }
      );
    }
  );


// ============================================================
// STARTUP
// ============================================================

setMode("explore");

loadDocuments();