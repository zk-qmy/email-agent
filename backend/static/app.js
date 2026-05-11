const API_BASE = "";

function formatJson(data) {
    return JSON.stringify(data, null, 2);
}

function getInputValue(sectionContent, field) {
    const input = sectionContent.querySelector(
        `.input-field[data-var="${field}"]`,
    );
    return input ? input.value : "";
}

function interpolateEndpoint(endpoint, userId, sectionContent) {
    let result = endpoint;
    result = result.replace(/\{\{user_id\}\}/g, userId);
    result = result.replace(
        /\{\{email_id\}\}/g,
        getInputValue(sectionContent, "email_id"),
    );
    result = result.replace(
        /\{\{thread_id\}\}/g,
        getInputValue(sectionContent, "thread_id"),
    );
    result = result.replace(
        /\{\{event_id\}\}/g,
        getInputValue(sectionContent, "event_id"),
    );
    result = result.replace(
        /\{\{start_date\}\}/g,
        getInputValue(sectionContent, "start_date"),
    );
    result = result.replace(
        /\{\{end_date\}\}/g,
        getInputValue(sectionContent, "end_date"),
    );
    return result;
}

function interpolateBody(body, userId, sectionContent) {
    if (!body) return body;
    let result = body;
    result = result.replace(/\{\{user_id\}\}/g, userId);
    result = result.replace(
        /\{\{email\}\}/g,
        getInputValue(sectionContent, "email"),
    );
    result = result.replace(
        /\{\{password\}\}/g,
        getInputValue(sectionContent, "password"),
    );
    result = result.replace(
        /\{\{username\}\}/g,
        getInputValue(sectionContent, "username"),
    );
    result = result.replace(
        /\{\{email_id\}\}/g,
        getInputValue(sectionContent, "email_id"),
    );
    result = result.replace(
        /\{\{recipient_email\}\}/g,
        getInputValue(sectionContent, "recipient_email"),
    );
    result = result.replace(
        /\{\{subject\}\}/g,
        getInputValue(sectionContent, "subject"),
    );
    result = result.replace(
        /\{\{body\}\}/g,
        getInputValue(sectionContent, "body"),
    );
    result = result.replace(
        /\{\{thread_id\}\}/g,
        getInputValue(sectionContent, "thread_id"),
    );
    result = result.replace(
        /\{\{context\}\}/g,
        getInputValue(sectionContent, "context"),
    );
    result = result.replace(
        /\{\{date\}\}/g,
        getInputValue(sectionContent, "date"),
    );
    result = result.replace(
        /\{\{time\}\}/g,
        getInputValue(sectionContent, "time"),
    );
    result = result.replace(
        /\{\{message\}\}/g,
        getInputValue(sectionContent, "message"),
    );
    result = result.replace(
        /\{\{response\}\}/g,
        getInputValue(sectionContent, "response"),
    );
    result = result.replace(
        /\{\{text\}\}/g,
        getInputValue(sectionContent, "text"),
    );
    result = result.replace(
        /\{\{user_role\}\}/g,
        getInputValue(sectionContent, "user_role"),
    );
    result = result.replace(
        /\{\{cc\}\}/g,
        getInputValue(sectionContent, "cc"),
    );
    result = result.replace(
        /\{\{bcc\}\}/g,
        getInputValue(sectionContent, "bcc"),
    );
    result = result.replace(
        /\{\{start_time\}\}/g,
        getInputValue(sectionContent, "start_time"),
    );
    result = result.replace(
        /\{\{duration_minutes\}\}/g,
        getInputValue(sectionContent, "duration_minutes"),
    );
    result = result.replace(
        /\{\{title\}\}/g,
        getInputValue(sectionContent, "title"),
    );
    result = result.replace(
        /\{\{description\}\}/g,
        getInputValue(sectionContent, "description"),
    );
    result = result.replace(
        /\{\{location\}\}/g,
        getInputValue(sectionContent, "location"),
    );
    result = result.replace(
        /\{\{event_id\}\}/g,
        getInputValue(sectionContent, "event_id"),
    );
    result = result.replace(
        /\{\{start_date\}\}/g,
        getInputValue(sectionContent, "start_date"),
    );
    result = result.replace(
        /\{\{end_date\}\}/g,
        getInputValue(sectionContent, "end_date"),
    );
    result = result.replace(
        /\{\{end_time\}\}/g,
        getInputValue(sectionContent, "end_time"),
    );
    result = result.replace(
        /\{\{student_request\}\}/g,
        getInputValue(sectionContent, "student_request"),
    );
    result = result.replace(
        /\{\{question\}\}/g,
        getInputValue(sectionContent, "question"),
    );
    result = result.replace(
        /\{\{query\}\}/g,
        getInputValue(sectionContent, "query"),
    );
    result = result.replace(
        /\{\{top_k\}\}/g,
        getInputValue(sectionContent, "top_k"),
    );
    return result;
}

async function callApi(endpoint, options = {}) {
    const startTime = Date.now();
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
            ...options,
        });

        const elapsed = Date.now() - startTime;
        const contentType = response.headers.get("content-type") || "";

        let data;
        let isJson = contentType.includes("application/json");

        if (isJson) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        const result = {
            status: response.status,
            statusText: response.statusText,
            time: `${elapsed}ms`,
            data: data,
        };

        return result;
    } catch (error) {
        return {
            status: 0,
            statusText: "Error",
            time: `${Date.now() - startTime}ms`,
            error: error.message,
        };
    }
}

function displayResponse(result, targetId = "response-output") {
    const output = document.getElementById(targetId);
    const statusColor =
        result.status >= 200 && result.status < 300 ? "#10b981" : "#ef4444";

    output.innerHTML = `<span style="color: ${statusColor}">${result.status} ${result.statusText}</span> (${result.time})\n\n${formatJson(result.data || result.error)}`;
}

function displayError(error) {
    const output = document.getElementById("response-output");
    output.innerHTML = `<span style="color: #ef4444">Error</span>\n\n${error}`;
}

async function checkAgentStatus() {
    const indicator = document.getElementById("agent-status-indicator");
    const text = document.getElementById("agent-status-text");

    try {
        const result = await callApi("/api/agent/health");
        if (result.status === 200 && result.data.status === "online") {
            indicator.className = "status-indicator online";
            text.textContent = "Agent: Online";
        } else {
            indicator.className = "status-indicator offline";
            text.textContent = "Agent: Offline";
        }
    } catch (e) {
        indicator.className = "status-indicator offline";
        text.textContent = "Agent: Offline";
    }
}

async function loadUsers() {
    const select = document.getElementById("user-select");
    select.innerHTML = '<option value="">Loading...</option>';

    try {
        const result = await callApi("/api/auth/users");

        if (result.status >= 200 && result.status < 300 && result.data.users) {
            const users = result.data.users;
            if (users.length === 0) {
                select.innerHTML = '<option value="">No users found</option>';
            } else {
                select.innerHTML = users
                    .map(
                        (u) =>
                            `<option value="${u.id}">${u.username} (${u.email})</option>`,
                    )
                    .join("");

                select.selectedIndex = 0;
                if (select.value) {
                    select.dispatchEvent(new Event("change"));
                }
            }
        } else {
            select.innerHTML = '<option value="">Error loading users</option>';
        }
    } catch (error) {
        select.innerHTML = '<option value="">Error loading users</option>';
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadUsers();
    checkAgentStatus();

    setInterval(checkAgentStatus, 30000);

    document.getElementById("refresh-users").addEventListener("click", () => {
        loadUsers();
    });

    document
        .getElementById("user-select")
        .addEventListener("change", async (event) => {
            const userId = event.target.value;
            if (!userId) return;

            connectWebSocket(userId);

            const result = await callApi(`/api/auth/users/${userId}`);

            if (result.status === 200 && result.data && result.data.user) {
                const user = result.data.user;

                const authTab = document.getElementById("auth-tab");
                if (!authTab) return;

                const inputs = authTab.querySelectorAll(".input-field");

                if (inputs.length >= 6) {
                    inputs[3].value = user.username;
                    inputs[4].value = user.email;
                }
            }
        });

    let ws = null;
    let currentUserId = null;

    function connectWebSocket(userId) {
        if (ws && ws.readyState === WebSocket.OPEN && currentUserId === userId) {
            return;
        }

        if (ws) {
            ws.close();
        }

        currentUserId = userId;
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        ws = new WebSocket(`${protocol}//${window.location.host}/ws/push/${userId}`);

        ws.onopen = () => {
            console.log("[ws] Connected");
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log("[ws] Received:", data);
                displayWsEvent(data);
            } catch (e) {
                console.error("[ws] Parse error:", e);
            }
        };

        ws.onclose = () => {
            console.log("[ws] Disconnected");
            if (currentUserId) {
                setTimeout(() => connectWebSocket(currentUserId), 3000);
            }
        };

        ws.onerror = (error) => {
            console.error("[ws] Error:", error);
        };
    }

    function displayWsEvent(data) {
        const output = document.getElementById("agent-response-output");
        const color = data.event?.includes("_error") ? "#ef4444" : "#10b981";
        const eventInfo = `<span style="color: ${color}">[${data.event}]</span>`;
        output.innerHTML = `${eventInfo}\n\n${formatJson(data)}`;
    }

    document.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document
                .querySelectorAll(".tab-btn")
                .forEach((b) => b.classList.remove("active"));
            document
                .querySelectorAll(".tab-pane")
                .forEach((p) => p.classList.remove("active"));
            btn.classList.add("active");
            document
                .getElementById(`${btn.dataset.tab}-tab`)
                .classList.add("active");
        });
    });

    document.querySelectorAll(".section-title").forEach((title) => {
        title.addEventListener("click", () => {
            title.classList.toggle("collapsed");
            const content = title.nextElementSibling;
            content.classList.toggle("hidden");
        });
    });

    document.querySelectorAll(".test-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const method = btn.dataset.method;
            let endpoint = btn.dataset.endpoint;
            let body = btn.dataset.body;

            const userSelect = document.getElementById("user-select");
            const userId = userSelect.value;

            if (endpoint === "/api/agent/health") {
                const result = await callApi(endpoint);
                displayResponse(result);
                return;
            }

            const sectionContent = btn.closest(".section-content");

            endpoint = interpolateEndpoint(endpoint, userId, sectionContent);
            body = interpolateBody(body, userId, sectionContent);

            if (body && (method === "POST" || method === "PUT")) {
                try {
                    const parsed = JSON.parse(body);
                    ["cc", "bcc"].forEach(field => {
                        const v = parsed[field];
                        if (!v || v === "") {
                            delete parsed[field];
                        } else if (typeof v === "string") {
                            parsed[field] = v.split(",").map(s => s.trim()).filter(Boolean);
                        }
                    });
                    body = JSON.stringify(parsed);
                } catch (e) {}
            }

            const options = { method };
            if (body && method !== "GET") {
                options.body = body;
            }

            displayResponse({
                status: "...",
                statusText: "Loading",
                time: "...",
                data: { loading: true },
            });

            const result = await callApi(endpoint, options);
            displayResponse(result);

            if (result.status >= 200 && result.status < 300) {
                if (
                    endpoint === "/api/auth/signup" ||
                    (endpoint.includes("/api/auth/users/") &&
                        (method === "PUT" || method === "DELETE"))
                ) {
                    loadUsers();
                }
                if (method === "POST" && endpoint === "/api/agent/thread" && result.data?.thread_id) {
                    const threadInput = sectionContent.querySelector('.input-field[data-var="thread_id"]');
                    if (threadInput) threadInput.value = result.data.thread_id;
                }
            }
        });
    });

    document.getElementById("clear-response").addEventListener("click", () => {
        document.getElementById("response-output").textContent = "";
    });

    document.getElementById("clear-agent-response").addEventListener("click", () => {
        document.getElementById("agent-response-output").textContent = "";
    });

    document.getElementById("summarize-thread-btn").addEventListener("click", async () => {
        const userSelect = document.getElementById("user-select");
        const userId = userSelect.value;
        const targetOutput = "agent-response-output";
        if (!userId) {
            displayResponse({ status: 400, statusText: "Bad Request", time: "0ms", data: { error: "No user selected" } }, targetOutput);
            return;
        }

        const sectionContent = document.getElementById("emails-threads-section");
        const threadId = getInputValue(sectionContent, "thread_id");
        if (!threadId) {
            displayResponse({ status: 400, statusText: "Bad Request", time: "0ms", data: { error: "No thread_id entered" } }, targetOutput);
            return;
        }

        displayResponse({ status: "...", statusText: "Summarizing...", time: "...", data: { loading: true } }, targetOutput);

        const result = await callApi("/api/agent/draft", {
            method: "POST",
            body: JSON.stringify({
                user_id: parseInt(userId),
                prompt: `[User ID: ${userId}] Summarize the email thread with ID: ${threadId}`,
            }),
        });

        displayResponse(result, targetOutput);
    });

    document.querySelectorAll(".test-btn[data-action]").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const action = btn.dataset.action;
            const sectionContent = btn.closest(".section-content");
            const fileInput = sectionContent?.querySelector('.input-file[data-var="pdf_file"]');
            const file = fileInput?.files?.[0];

            if (!file) {
                displayResponse({ status: 400, statusText: "Bad Request", time: "0ms", data: { error: "No PDF file selected" } });
                return;
            }

            displayResponse({ status: "...", statusText: "Loading", time: "...", data: { loading: true } });

            const formData = new FormData();
            formData.append("file", file);

            if (action === "pdf-validate-upload") {
                const role = getInputValue(sectionContent, "user_role");
                formData.append("user_role", role);
            }

            const startTime = Date.now();
            try {
                const response = await fetch(`/api/agent/pdf/${action === "pdf-validate-upload" ? "validate-upload" : "parse"}`, {
                    method: "POST",
                    body: formData,
                });
                const elapsed = Date.now() - startTime;
                const contentType = response.headers.get("content-type") || "";
                let data;
                if (contentType.includes("application/json")) {
                    data = await response.json();
                } else {
                    data = await response.text();
                }
                displayResponse({ status: response.status, statusText: response.statusText, time: `${elapsed}ms`, data });
            } catch (error) {
                displayResponse({ status: 0, statusText: "Error", time: `${Date.now() - startTime}ms`, error: error.message });
            }
        });
    });
});