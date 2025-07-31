// Глобальные переменные
let currentUser = null;
let authToken = localStorage.getItem('authToken');

// API базовый URL
const API_BASE = '/api';

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Проверяем авторизацию
    if (authToken) {
        checkAuth();
    } else {
        showLoginSection();
    }

    // Обработчики событий
    setupEventListeners();
    
    // Загружаем данные для фильтров
    loadFilterData();
}

function setupEventListeners() {
    // Навигация
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            showSection(section);
        });
    });

    // Форма входа
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    
    // Кнопка выхода
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Поиск и фильтры
    document.getElementById('studentSearch').addEventListener('input', debounce(filterStudents, 300));
    document.getElementById('textbookSearch').addEventListener('input', debounce(filterTextbooks, 300));
    document.getElementById('gradeFilter').addEventListener('change', filterStudents);
    document.getElementById('subjectFilter').addEventListener('change', filterTextbooks);
    document.getElementById('transactionTypeFilter').addEventListener('change', filterTransactions);
    document.getElementById('dateFilter').addEventListener('change', filterTransactions);
}

// Авторизация
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
        });

        const data = await response.json();
        
        if (response.ok) {
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            currentUser = { username };
            showDashboard();
            loadDashboardData();
        } else {
            showError('loginError', data.detail || 'Ошибка входа');
        }
    } catch (error) {
        showError('loginError', 'Ошибка подключения к серверу');
    }
}

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            currentUser = await response.json();
            showDashboard();
            loadDashboardData();
        } else {
            localStorage.removeItem('authToken');
            authToken = null;
            showLoginSection();
        }
    } catch (error) {
        localStorage.removeItem('authToken');
        authToken = null;
        showLoginSection();
    }
}

function handleLogout() {
    localStorage.removeItem('authToken');
    authToken = null;
    currentUser = null;
    showLoginSection();
}

// Навигация
function showSection(sectionName) {
    // Скрываем все секции
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Убираем активный класс у всех ссылок
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Показываем нужную секцию
    const targetSection = document.getElementById(`${sectionName}Section`);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Активируем ссылку
    const activeLink = document.querySelector(`[data-section="${sectionName}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
    
    // Загружаем данные для секции
    loadSectionData(sectionName);
}

function showLoginSection() {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById('loginSection').classList.add('active');
}

function showDashboard() {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById('dashboardSection').classList.add('active');
    
    // Активируем первую ссылку в навигации
    const firstLink = document.querySelector('.nav-link');
    if (firstLink) {
        firstLink.classList.add('active');
    }
}

// Загрузка данных
async function loadDashboardData() {
    try {
        // Загружаем статистику
        const [studentsResponse, textbooksResponse, transactionsResponse, reportsResponse] = await Promise.all([
            fetch(`${API_BASE}/students`, { headers: { 'Authorization': `Bearer ${authToken}` } }),
            fetch(`${API_BASE}/textbooks`, { headers: { 'Authorization': `Bearer ${authToken}` } }),
            fetch(`${API_BASE}/transactions`, { headers: { 'Authorization': `Bearer ${authToken}` } }),
            fetch(`${API_BASE}/damage-reports`, { headers: { 'Authorization': `Bearer ${authToken}` } })
        ]);

        if (studentsResponse.ok) {
            const students = await studentsResponse.json();
            document.getElementById('totalStudents').textContent = students.length;
        }

        if (textbooksResponse.ok) {
            const textbooks = await textbooksResponse.json();
            document.getElementById('totalTextbooks').textContent = textbooks.length;
        }

        if (transactionsResponse.ok) {
            const transactions = await transactionsResponse.json();
            const activeTransactions = transactions.filter(t => t.status === 'completed' && t.transaction_type === 'issue');
            document.getElementById('activeTransactions').textContent = activeTransactions.length;
        }

        if (reportsResponse.ok) {
            const reports = await reportsResponse.json();
            const pendingReports = reports.filter(r => r.status === 'pending');
            document.getElementById('pendingReports').textContent = pendingReports.length;
        }
    } catch (error) {
        console.error('Ошибка загрузки данных дашборда:', error);
    }
}

function loadSectionData(sectionName) {
    switch (sectionName) {
        case 'students':
            loadStudents();
            break;
        case 'textbooks':
            loadTextbooks();
            break;
        case 'transactions':
            loadTransactions();
            break;
        case 'bot-management':
            testBotConnection();
            break;
    }
}

async function loadStudents() {
    try {
        const response = await fetch(`${API_BASE}/students`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const students = await response.json();
            renderStudentsTable(students);
            populateGradeFilter(students);
        }
    } catch (error) {
        console.error('Ошибка загрузки учеников:', error);
    }
}

async function loadTextbooks() {
    try {
        const response = await fetch(`${API_BASE}/textbooks`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const textbooks = await response.json();
            renderTextbooksTable(textbooks);
            populateSubjectFilter(textbooks);
        }
    } catch (error) {
        console.error('Ошибка загрузки учебников:', error);
    }
}

async function loadTransactions() {
    try {
        const response = await fetch(`${API_BASE}/transactions`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const transactions = await response.json();
            renderTransactionsTable(transactions);
        }
    } catch (error) {
        console.error('Ошибка загрузки транзакций:', error);
    }
}

// Рендеринг таблиц
function renderStudentsTable(students) {
    const tbody = document.getElementById('studentsTableBody');
    tbody.innerHTML = '';

    students.forEach(student => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${student.id}</td>
            <td>${student.full_name}</td>
            <td>${student.grade}</td>
            <td>${student.phone || '-'}</td>
            <td>${student.parent_phone || '-'}</td>
            <td>${student.max_user_id ? '✓' : '✗'}</td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="editStudent(${student.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger btn-sm" onclick="deleteStudent(${student.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function renderTextbooksTable(textbooks) {
    const tbody = document.getElementById('textbooksTableBody');
    tbody.innerHTML = '';

    textbooks.forEach(textbook => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${textbook.id}</td>
            <td><code>${textbook.qr_code}</code></td>
            <td>${textbook.subject}</td>
            <td>${textbook.title}</td>
            <td>${textbook.author}</td>
            <td>${textbook.year}</td>
            <td>${textbook.is_active ? 'Активен' : 'Неактивен'}</td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="editTextbook(${textbook.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-info btn-sm" onclick="downloadQR(${textbook.id})">
                    <i class="fas fa-qrcode"></i>
                </button>
                <button class="btn btn-danger btn-sm" onclick="deleteTextbook(${textbook.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function renderTransactionsTable(transactions) {
    const tbody = document.getElementById('transactionsTableBody');
    tbody.innerHTML = '';

    transactions.forEach(transaction => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${transaction.id}</td>
            <td>${transaction.transaction_type === 'issue' ? 'Выдача' : 'Возврат'}</td>
            <td>${transaction.student?.full_name || 'Неизвестно'}</td>
            <td>${transaction.textbook?.title || 'Неизвестно'}</td>
            <td>${new Date(transaction.issued_at).toLocaleDateString()}</td>
            <td>${transaction.status === 'completed' ? 'Завершена' : 'В процессе'}</td>
            <td>
                <button class="btn btn-info btn-sm" onclick="viewTransactionDetails(${transaction.id})">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Фильтры
function populateGradeFilter(students) {
    const grades = [...new Set(students.map(s => s.grade))].sort();
    const select = document.getElementById('gradeFilter');
    
    select.innerHTML = '<option value="">Все классы</option>';
    grades.forEach(grade => {
        const option = document.createElement('option');
        option.value = grade;
        option.textContent = grade;
        select.appendChild(option);
    });
}

function populateSubjectFilter(textbooks) {
    const subjects = [...new Set(textbooks.map(t => t.subject))].sort();
    const select = document.getElementById('subjectFilter');
    
    select.innerHTML = '<option value="">Все предметы</option>';
    subjects.forEach(subject => {
        const option = document.createElement('option');
        option.value = subject;
        option.textContent = subject;
        select.appendChild(option);
    });
}

function filterStudents() {
    const searchTerm = document.getElementById('studentSearch').value.toLowerCase();
    const gradeFilter = document.getElementById('gradeFilter').value;
    const rows = document.querySelectorAll('#studentsTableBody tr');

    rows.forEach(row => {
        const name = row.cells[1].textContent.toLowerCase();
        const grade = row.cells[2].textContent;
        
        const matchesSearch = name.includes(searchTerm);
        const matchesGrade = !gradeFilter || grade === gradeFilter;
        
        row.style.display = matchesSearch && matchesGrade ? '' : 'none';
    });
}

function filterTextbooks() {
    const searchTerm = document.getElementById('textbookSearch').value.toLowerCase();
    const subjectFilter = document.getElementById('subjectFilter').value;
    const rows = document.querySelectorAll('#textbooksTableBody tr');

    rows.forEach(row => {
        const title = row.cells[3].textContent.toLowerCase();
        const subject = row.cells[2].textContent;
        
        const matchesSearch = title.includes(searchTerm);
        const matchesSubject = !subjectFilter || subject === subjectFilter;
        
        row.style.display = matchesSearch && matchesSubject ? '' : 'none';
    });
}

function filterTransactions() {
    const typeFilter = document.getElementById('transactionTypeFilter').value;
    const dateFilter = document.getElementById('dateFilter').value;
    const rows = document.querySelectorAll('#transactionsTableBody tr');

    rows.forEach(row => {
        const type = row.cells[1].textContent;
        const date = row.cells[4].textContent;
        
        const matchesType = !typeFilter || type === (typeFilter === 'issue' ? 'Выдача' : 'Возврат');
        const matchesDate = !dateFilter || date === new Date(dateFilter).toLocaleDateString();
        
        row.style.display = matchesType && matchesDate ? '' : 'none';
    });
}

// Модальные окна
function showModal(title, content) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = content;
    document.getElementById('modalOverlay').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modalOverlay').style.display = 'none';
}

function showAddStudentModal() {
    const content = `
        <form id="addStudentForm">
            <div class="form-group">
                <label for="firstName">Имя:</label>
                <input type="text" id="firstName" name="first_name" required>
            </div>
            <div class="form-group">
                <label for="lastName">Фамилия:</label>
                <input type="text" id="lastName" name="last_name" required>
            </div>
            <div class="form-group">
                <label for="middleName">Отчество:</label>
                <input type="text" id="middleName" name="middle_name">
            </div>
            <div class="form-group">
                <label for="grade">Класс:</label>
                <input type="text" id="grade" name="grade" required>
            </div>
            <div class="form-group">
                <label for="phone">Телефон:</label>
                <input type="tel" id="phone" name="phone">
            </div>
            <div class="form-group">
                <label for="parentPhone">Телефон родителя:</label>
                <input type="tel" id="parentPhone" name="parent_phone">
            </div>
            <div class="form-group">
                <button type="submit" class="btn btn-primary">Добавить ученика</button>
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Отмена</button>
            </div>
        </form>
    `;
    
    showModal('Добавить ученика', content);
    
    document.getElementById('addStudentForm').addEventListener('submit', handleAddStudent);
}

function showAddTextbookModal() {
    const content = `
        <form id="addTextbookForm">
            <div class="form-group">
                <label for="subject">Предмет:</label>
                <input type="text" id="subject" name="subject" required>
            </div>
            <div class="form-group">
                <label for="title">Название:</label>
                <input type="text" id="title" name="title" required>
            </div>
            <div class="form-group">
                <label for="author">Автор:</label>
                <input type="text" id="author" name="author" required>
            </div>
            <div class="form-group">
                <label for="year">Год издания:</label>
                <input type="number" id="year" name="year" min="1900" max="2030" required>
            </div>
            <div class="form-group">
                <label for="isbn">ISBN:</label>
                <input type="text" id="isbn" name="isbn">
            </div>
            <div class="form-group">
                <button type="submit" class="btn btn-primary">Добавить учебник</button>
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Отмена</button>
            </div>
        </form>
    `;
    
    showModal('Добавить учебник', content);
    
    document.getElementById('addTextbookForm').addEventListener('submit', handleAddTextbook);
}

// Обработчики форм
async function handleAddStudent(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const studentData = Object.fromEntries(formData.entries());
    
    try {
        const response = await fetch(`${API_BASE}/students`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(studentData)
        });

        if (response.ok) {
            closeModal();
            loadStudents();
            showSuccess('Ученик успешно добавлен');
        } else {
            const error = await response.json();
            showError('modalError', error.detail || 'Ошибка добавления ученика');
        }
    } catch (error) {
        showError('modalError', 'Ошибка подключения к серверу');
    }
}

async function handleAddTextbook(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const textbookData = Object.fromEntries(formData.entries());
    
    try {
        const response = await fetch(`${API_BASE}/textbooks`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(textbookData)
        });

        if (response.ok) {
            closeModal();
            loadTextbooks();
            showSuccess('Учебник успешно добавлен');
        } else {
            const error = await response.json();
            showError('modalError', error.detail || 'Ошибка добавления учебника');
        }
    } catch (error) {
        showError('modalError', 'Ошибка подключения к серверу');
    }
}

// Бот
async function testBotConnection() {
    try {
        const response = await fetch(`${API_BASE}/bot/test-connection`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        const result = await response.json();
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');

        if (result.status === 'success') {
            statusDot.classList.add('connected');
            statusText.textContent = 'Подключен';
        } else {
            statusDot.classList.remove('connected');
            statusText.textContent = 'Ошибка подключения';
        }
    } catch (error) {
        console.error('Ошибка тестирования подключения бота:', error);
    }
}

async function getBotInfo() {
    try {
        const response = await fetch(`${API_BASE}/bot/info`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const info = await response.json();
            const content = `
                <div class="bot-info">
                    <p><strong>ID:</strong> ${info.id || 'Неизвестно'}</p>
                    <p><strong>Имя:</strong> ${info.name || 'Неизвестно'}</p>
                    <p><strong>Описание:</strong> ${info.description || 'Не указано'}</p>
                    <p><strong>Статус:</strong> ${info.status || 'Неизвестно'}</p>
                </div>
            `;
            showModal('Информация о боте', content);
        }
    } catch (error) {
        console.error('Ошибка получения информации о боте:', error);
    }
}

// Отчеты
async function generateIssueReport() {
    try {
        const response = await fetch(`${API_BASE}/reports/issue-summary`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            downloadReport(data, 'issue_report.json', 'application/json');
        }
    } catch (error) {
        console.error('Ошибка генерации отчета:', error);
    }
}

async function generateNotReturnedReport() {
    try {
        const response = await fetch(`${API_BASE}/reports/not-returned`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            downloadReport(data, 'not_returned_report.json', 'application/json');
        }
    } catch (error) {
        console.error('Ошибка генерации отчета:', error);
    }
}

async function generateDamageReport() {
    try {
        const response = await fetch(`${API_BASE}/reports/damage-summary`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            downloadReport(data, 'damage_report.json', 'application/json');
        }
    } catch (error) {
        console.error('Ошибка генерации отчета:', error);
    }
}

function downloadReport(data, filename, contentType) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Утилиты
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}

function showSuccess(message) {
    // Можно добавить toast уведомления
    alert(message);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Загрузка данных для фильтров
function loadFilterData() {
    // Загружаем данные для фильтров при инициализации
    if (authToken) {
        loadStudents();
        loadTextbooks();
    }
} 