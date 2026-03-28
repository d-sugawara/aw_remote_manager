/**
 * 教員用モニターダッシュボード スクリプト
 */

let AppConfig = {
    base_url: "http://localhost/aw_remote_manager/server/public/api"
};

// 外部ファイル config.js から読み込まれた CONFIG オブジェクトが存在すれば上書き
if (typeof CONFIG !== "undefined") {
    Object.assign(AppConfig, CONFIG);
}

const API_BASE_URL = AppConfig.base_url;

let state = {
    isAutoUpdateSelected: true,
    lastTimestamps: {},
    currentStudents: [],
    filterValue: ""
};

let updateIntervalId = null;

const elements = {
    grid: document.getElementById("students-grid"),
    filterInput: document.getElementById("prefix-filter"),
    toggleUpdateBtn: document.getElementById("toggle-update")
};

/**
 * 初期化処理
 */
function init() {
    // フィルタ入力
    elements.filterInput.addEventListener("input", (e) => {
        state.filterValue = e.target.value.trim();
        fetchStudents(true); // 即時更新かつ再構築
    });

    // 自動更新ボタン
    elements.toggleUpdateBtn.addEventListener("click", () => {
        state.isAutoUpdateSelected = !state.isAutoUpdateSelected;
        
        if (state.isAutoUpdateSelected) {
            elements.toggleUpdateBtn.textContent = "自動更新ON";
            elements.toggleUpdateBtn.classList.add("active");
            startAutoUpdate();
            fetchStudents();
        } else {
            elements.toggleUpdateBtn.textContent = "自動更新OFF";
            elements.toggleUpdateBtn.classList.remove("active");
            stopAutoUpdate();
        }
    });

    // 初回読み込み
    startAutoUpdate();
    fetchStudents(true);

    // モーダル背景または閉じるボタンで閉じる
    document.getElementById("image-modal").addEventListener("click", (e) => {
        if (e.target.id === "image-modal" || e.target.id === "modal-close") {
            closeModal();
        }
    });
}

/**
 * モーダル表示
 */
function openModal(src) {
    const modal = document.getElementById("image-modal");
    const modalImg = document.getElementById("modal-img");
    modalImg.src = src;
    modal.classList.add("active");
}

/**
 * モーダルを閉じる
 */
function closeModal() {
    document.getElementById("image-modal").classList.remove("active");
}

/**
 * 自動更新の開始
 */
function startAutoUpdate() {
    if (updateIntervalId === null) {
        updateIntervalId = setInterval(() => {
            fetchStudents(false); // 差分更新
        }, 1000);
    }
}

/**
 * 自動更新の停止
 */
function stopAutoUpdate() {
    if (updateIntervalId !== null) {
        clearInterval(updateIntervalId);
        updateIntervalId = null;
    }
}

/**
 * 学生データの取得
 * @param {boolean} forceRebuild 全面的な再構築を行うかどうか
 */
async function fetchStudents(forceRebuild = false) {
    try {
        const url = new URL(`${API_BASE_URL}/teacher/students`);
        if (state.filterValue) {
            url.searchParams.append("prefix", state.filterValue);
        }
        // キャッシュ回避
        url.searchParams.append("_t", Date.now());

        const response = await fetch(url, { cache: "no-store" });
        if (!response.ok) {
            console.error("学生データの取得に失敗しました");
            return;
        }

        const data = await response.json();
        
        // 前回のリストと学生番号の並びが違う場合（人数増減やフィルタ変更時）は再構築
        const currentIds = data.map(s => s.student_number).join(",");
        const oldIds = state.currentStudents.map(s => s.student_number).join(",");
        
        if (forceRebuild || currentIds !== oldIds) {
            rebuildGrid(data);
            state.currentStudents = data;
        } else {
            // 人数が同じなら画像のみ更新
            updateImagesOnly(data);
        }

    } catch (error) {
        console.error("学生データの取得中にエラーが発生しました:", error);
    }
}

/**
 * グリッド全体の再構築
 */
function rebuildGrid(students) {
    elements.grid.innerHTML = "";
    state.lastTimestamps = {};

    if (students.length === 0) {
        const msg = document.createElement("div");
        msg.className = "no-results";
        msg.textContent = "該当する学生が見つかりません。";
        elements.grid.appendChild(msg);
        return;
    }

    students.forEach(student => {
        const card = createStudentCard(student);
        elements.grid.appendChild(card);
        
        if (student.updated_at) {
            state.lastTimestamps[student.student_number] = student.updated_at;
        }
    });
}

/**
 * 学生カードを作成
 */
function createStudentCard(student) {
    const card = document.createElement("div");
    card.className = "student-card";
    card.id = `student-card-${student.student_number}`;

    const capWrap = document.createElement("div");
    capWrap.className = "capture-container";
    capWrap.id = `capture-container-${student.student_number}`;

    if (student.updated_at) {
        const time = new Date(student.updated_at).getTime();
        const imgSrc = `${student.image_url}?t=${time}`;
        capWrap.innerHTML = `<img src="${imgSrc}" alt="${student.name}の画面" class="capture-img" id="capture-img-${student.student_number}" />`;
    } else {
        capWrap.innerHTML = `
            <div class="no-capture" id="no-capture-${student.student_number}">
                <div class="no-capture-icon">✕</div>
                <div>この学生はアプリを起動していません</div>
            </div>
        `;
    }

    const info = document.createElement("div");
    info.className = "student-info";
    info.innerHTML = `
        <span class="student-name">${student.student_number} ${escapeHtml(student.name)}</span>
        <span class="student-status ${student.updated_at ? 'online' : 'offline'}" id="status-${student.student_number}">
            ${student.updated_at ? 'オンライン' : 'オフライン'}
        </span>
    `;

    // クリックで拡大
    capWrap.addEventListener("click", () => {
        const img = document.getElementById(`capture-img-${student.student_number}`);
        if (img && student.updated_at) {
            openModal(img.src);
        }
    });

    card.appendChild(capWrap);
    card.appendChild(info);
    
    return card;
}

/**
 * 画像とステータスのみを更新
 */
function updateImagesOnly(students) {
    students.forEach(student => {
        const lastTime = state.lastTimestamps[student.student_number];
        const currentTime = student.updated_at;

        if (currentTime !== lastTime) {
            state.lastTimestamps[student.student_number] = currentTime;
            
            const capWrap = document.getElementById(`capture-container-${student.student_number}`);
            const statusEl = document.getElementById(`status-${student.student_number}`);
            
            if (!capWrap) return;

            if (currentTime) {
                const time = new Date(currentTime).getTime();
                const imgSrc = `${student.image_url}?t=${time}`;
                const img = document.getElementById(`capture-img-${student.student_number}`);
                
                if (img) {
                    img.src = imgSrc;
                } else {
                    // 前回Offlineだった場合などを考慮
                    capWrap.innerHTML = `<img src="${imgSrc}" alt="${student.name}の画面" class="capture-img" id="capture-img-${student.student_number}" />`;
                }

                if (statusEl) {
                    statusEl.className = "student-status online";
                    statusEl.textContent = "オンライン";
                }
            } else {
                // オフラインになった場合
                capWrap.innerHTML = `
                    <div class="no-capture" id="no-capture-${student.student_number}">
                        <div class="no-capture-icon">✕</div>
                        <div>この学生はアプリを起動していません</div>
                    </div>
                `;
                if (statusEl) {
                    statusEl.className = "student-status offline";
                    statusEl.textContent = "オフライン";
                }
            }
        }
    });
}

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", init);