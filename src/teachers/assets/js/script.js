const SECRET_KEY_STR = 'AwRemoteManagerSecretKey202611!!';
let AppConfig = {
    base_url: 'http://localhost/aw_remote_manager/server/public/api' // Fallback
};

if (typeof ENCRYPTED_CONFIG !== 'undefined') {
    try {
        const key = CryptoJS.enc.Utf8.parse(SECRET_KEY_STR);
        const raw = CryptoJS.enc.Base64.parse(ENCRYPTED_CONFIG);
        const iv = CryptoJS.lib.WordArray.create(raw.words.slice(0, 4), 16);
        const ciphertext = CryptoJS.lib.WordArray.create(raw.words.slice(4), raw.sigBytes - 16);
        
        const decrypted = CryptoJS.AES.decrypt({ ciphertext: ciphertext }, key, {
            iv: iv,
            mode: CryptoJS.mode.CBC,
            padding: CryptoJS.pad.Pkcs7
        });
        
        const jsonStr = decrypted.toString(CryptoJS.enc.Utf8);
        Object.assign(AppConfig, JSON.parse(jsonStr));
    } catch (e) {
        console.error('Failed to decrypt config.js. Using fallback.', e);
    }
}

const API_BASE_URL = AppConfig.base_url;

// 状態管理
let state = {
    isAutoUpdateSelected: true,
    lastTimestamps: {}, // student_number -> timestamp (string)
    currentStudents: [], // 描画済みの学生リスト
    filterValue: ''
};

let updateIntervalId = null;

// DOM要素の参照
const elements = {
    grid: document.getElementById('students-grid'),
    filterInput: document.getElementById('prefix-filter'),
    toggleUpdateBtn: document.getElementById('toggle-update'),
};

// 初期化
function init() {
    // イベントリスナー
    elements.filterInput.addEventListener('input', (e) => {
        state.filterValue = e.target.value.trim();
        // フィルタ変更時は即座にサーバーから再取得して再描画
        fetchStudents(true);
    });

    elements.toggleUpdateBtn.addEventListener('click', () => {
        state.isAutoUpdateSelected = !state.isAutoUpdateSelected;
        
        if (state.isAutoUpdateSelected) {
            elements.toggleUpdateBtn.textContent = '自動更新ON';
            elements.toggleUpdateBtn.classList.add('active');
            startAutoUpdate();
            fetchStudents(); // すぐに1回フェッチ
        } else {
            elements.toggleUpdateBtn.textContent = '自動更新OFF';
            elements.toggleUpdateBtn.classList.remove('active');
            stopAutoUpdate();
        }
    });

    // 最初のデータ取得開始
    startAutoUpdate();
    fetchStudents(true);

    // モーダルを閉じる処理
    const modal = document.getElementById('image-modal');
    modal.addEventListener('click', (e) => {
        if (e.target.id === 'image-modal' || e.target.id === 'modal-close') {
            closeModal();
        }
    });
}

function openModal(imgUrl) {
    const modal = document.getElementById('image-modal');
    const modalImg = document.getElementById('modal-img');
    modalImg.src = imgUrl;
    modal.classList.add('active');
}

function closeModal() {
    const modal = document.getElementById('image-modal');
    modal.classList.remove('active');
}

// 自動更新の開始
function startAutoUpdate() {
    if (updateIntervalId === null) {
        updateIntervalId = setInterval(() => {
            fetchStudents(false);
        }, 1000);
    }
}

// 自動更新の停止
function stopAutoUpdate() {
    if (updateIntervalId !== null) {
        clearInterval(updateIntervalId);
        updateIntervalId = null;
    }
}

// 学生データのフェッチ処理
async function fetchStudents(forceRebuild = false) {
    try {
        const url = new URL(`${API_BASE_URL}/teacher/students`);
        if (state.filterValue) {
            url.searchParams.append('prefix', state.filterValue);
        }
        url.searchParams.append('_t', Date.now());

        const response = await fetch(url, { cache: 'no-store' });
        if (!response.ok) {
            console.error('Failed to fetch students data');
            return;
        }

        const students = await response.json();
        
        // リストの変化を検知
        const studentNumbers = students.map(s => s.student_number).join(',');
        const currentStudentNumbers = state.currentStudents.map(s => s.student_number).join(',');
        
        if (forceRebuild || studentNumbers !== currentStudentNumbers) {
            // 学生が増減/入れ替わった場合は全体を再構築
            rebuildGrid(students);
            state.currentStudents = students;
        } else {
            // リストの構造が変わっていない場合は、各セルの画像タイムスタンプだけチェック
            updateImagesOnly(students);
        }
        
    } catch (error) {
        console.error('Error fetching students:', error);
    }
}

// グリッド全体の再描画
function rebuildGrid(students) {
    elements.grid.innerHTML = ''; // クリア
    state.lastTimestamps = {}; // キャッシュリセット

    if (students.length === 0) {
        const emptyMsg = document.createElement('div');
        emptyMsg.style.gridColumn = '1 / -1';
        emptyMsg.style.textAlign = 'center';
        emptyMsg.style.padding = '2rem';
        emptyMsg.style.color = 'var(--text-secondary)';
        emptyMsg.textContent = '該当する学生が見つかりません。';
        elements.grid.appendChild(emptyMsg);
        return;
    }

    students.forEach((student) => {
        const card = createStudentCard(student);
        elements.grid.appendChild(card);
        
        // タイムスタンプを保存
        if (student.updated_at) {
            state.lastTimestamps[student.student_number] = student.updated_at;
        }
    });
}

// 学生カードDOMの生成
function createStudentCard(student) {
    const card = document.createElement('div');
    card.className = 'student-card';
    card.id = `student-card-${student.student_number}`;

    const captureContainer = document.createElement('div');
    captureContainer.className = 'capture-container';
    captureContainer.id = `capture-container-${student.student_number}`;

    // 画像が存在するか(タイムスタンプがあるか)
    if (student.updated_at) {
        const imgUrl = `${student.image_url}?t=${new Date(student.updated_at).getTime()}`;
        captureContainer.innerHTML = `<img src="${imgUrl}" alt="${student.name}の画面" class="capture-img" id="capture-img-${student.student_number}" />`;
    } else {
        captureContainer.innerHTML = `
            <div class="no-capture" id="no-capture-${student.student_number}">
                <div class="no-capture-icon">✕</div>
                <div>この学生はアプリを起動していません</div>
            </div>
        `;
    }

    const info = document.createElement('div');
    info.className = 'student-info';
    info.innerHTML = `
        <span class="student-name">${student.student_number} ${escapeHtml(student.name)}</span>
        <span class="student-status ${student.updated_at ? 'online' : 'offline'}" id="status-${student.student_number}">
            ${student.updated_at ? 'Online' : 'Offline'}
        </span>
    `;

    // クリックで拡大表示
    captureContainer.style.cursor = 'pointer';
    captureContainer.addEventListener('click', () => {
        const img = document.getElementById(`capture-img-${student.student_number}`);
        if (img && student.updated_at) {
            openModal(img.src);
        }
    });

    card.appendChild(captureContainer);
    card.appendChild(info);

    return card;
}

// タイムスタンプのみの更新（画像の再取得）
function updateImagesOnly(students) {
    students.forEach((student) => {
        const currentTimestamp = state.lastTimestamps[student.student_number];
        const newTimestamp = student.updated_at;

        if (newTimestamp !== currentTimestamp) {
            // 更新があった場合
            state.lastTimestamps[student.student_number] = newTimestamp;
            
            const container = document.getElementById(`capture-container-${student.student_number}`);
            const statusEl = document.getElementById(`status-${student.student_number}`);

            if (!container) return;

            if (newTimestamp) {
                // 新しいタイムスタンプに基づき画像URLを更新
                const imgUrl = `${student.image_url}?t=${new Date(newTimestamp).getTime()}`;
                
                // 既存のimg要素があればsrcを更新、無ければ生成("アプリ起動していない"表示からの復帰)
                const existingImg = document.getElementById(`capture-img-${student.student_number}`);
                if (existingImg) {
                    existingImg.src = imgUrl;
                } else {
                    container.innerHTML = `<img src="${imgUrl}" alt="${student.name}の画面" class="capture-img" id="capture-img-${student.student_number}" />`;
                }

                // Status表示の更新
                if (statusEl) {
                    statusEl.className = 'student-status online';
                    statusEl.textContent = 'Online';
                }
            } else {
                // タイムスタンプが無くなった (滅多にないが画像削除時など)
                container.innerHTML = `
                    <div class="no-capture" id="no-capture-${student.student_number}">
                        <div class="no-capture-icon">✕</div>
                        <div>この学生はアプリを起動していません</div>
                    </div>
                `;
                
                if (statusEl) {
                    statusEl.className = 'student-status offline';
                    statusEl.textContent = 'Offline';
                }
            }
        }
    });
}

// 簡易XSS対策
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// アプリ起動
document.addEventListener('DOMContentLoaded', init);
