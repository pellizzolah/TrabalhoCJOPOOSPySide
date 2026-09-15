import sys
import re
import sqlite3
import requests
from datetime import datetime

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QLabel, QLineEdit,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QComboBox, QHeaderView, QMessageBox, QGroupBox,
                               QFileDialog, QStatusBar, QStyle)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QKeySequence, QShortcut

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# ==========================================
# CONFIGURAÇÕES GLOBAIS
# ==========================================
DB_PATH = "cadastro.db"

CORES = {
    "dark": {
        "bg": "#1e1e1e", "fg": "#e0e0e0", "accent": "#00bcd4",
        "input_bg": "#2d2d2d", "input_border": "#444",
        "btn_bg": "#333333", "btn_border": "#555", "btn_hover": "#444",
        "btn_salvar": "#28a745", "btn_salvar_hover": "#218838",
        "btn_excluir": "#dc3545", "btn_excluir_hover": "#c82333",
        "btn_pdf": "#e67e22", "btn_pdf_hover": "#d35400",
        "btn_editar": "#9c27b0",
        "table_bg": "#252525", "table_alt": "#2a2a2a", "grid": "#333",
        "header_bg": "#1a1a1a", "group_bg": "transparent",
        "status_bg": "#1a1a1a", "status_fg": "#888",
        "msg_bg": "#2d2d2d", "focus": "#00bcd4", "row_sel_fg": "#000",
    },
    "light": {
        "bg": "#f5f6fa", "fg": "#2f3640", "accent": "#0097e6",
        "input_bg": "#ffffff", "input_border": "#dcdde1",
        "btn_bg": "#f1f2f6", "btn_border": "#dcdde1", "btn_hover": "#eccc68",
        "btn_salvar": "#2ed573", "btn_salvar_hover": "#27ae60",
        "btn_excluir": "#ff4757", "btn_excluir_hover": "#e84118",
        "btn_pdf": "#e67e22", "btn_pdf_hover": "#d35400",
        "btn_editar": "#9c88ff",
        "table_bg": "#ffffff", "table_alt": "#f8f9fa", "grid": "#f1f2f6",
        "header_bg": "#f1f2f6", "group_bg": "#ffffff",
        "status_bg": "#f1f2f6", "status_fg": "#718093",
        "msg_bg": "#ffffff", "focus": "#0097e6", "row_sel_fg": "#ffffff",
    },
}

# ==========================================
# BANCO DE DADOS
# ==========================================
def db_execute(query, params=(), fetch=None):
    """Executa uma query no banco. fetch: 'one', 'all' ou None (commit)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    resultado = None
    if fetch == "one":
        resultado = cursor.fetchone()
    elif fetch == "all":
        resultado = cursor.fetchall()
    else:
        conn.commit()
    conn.close()
    return resultado

def init_db():
    db_execute('''
        CREATE TABLE IF NOT EXISTS pessoas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            email TEXT,
            celular TEXT,
            cep TEXT,
            logradouro TEXT,
            numero TEXT,
            complemento TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT,
            data_cadastro TEXT
        )
    ''')

# ==========================================
# FUNÇÕES UTILITÁRIAS
# ==========================================
def formatar_cpf(cpf):
    if not cpf: return ""
    cpf = str(cpf).zfill(11)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def formatar_celular(celular):
    if not celular: return ""
    celular = str(celular).zfill(11)
    return f"({celular[:2]}) {celular[2:7]}-{celular[7:]}"

def formatar_cep(cep):
    if not cep: return ""
    cep = str(cep).zfill(8)
    return f"{cep[:5]}-{cep[5:]}"

def limpar_formatacao(texto):
    return re.sub(r'\D', '', texto)

def validar_cpf(cpf):
    """Valida o CPF com o algoritmo oficial dos dígitos verificadores."""
    cpf = limpar_formatacao(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(cpf[j]) * ((i + 1) - j) for j in range(i))
        resto = (soma * 10) % 11
        if resto in (10, 11): resto = 0
        if resto != int(cpf[i]): return False
    return True

def montar_qss(c):
    """Gera o QSS a partir de um dicionário de cores."""
    return f"""
        QMainWindow, QWidget {{ background-color: {c['bg']}; color: {c['fg']}; font-family: 'Segoe UI', Arial; font-size: 14px; }}
        QGroupBox {{ border: 1px solid {c['input_border']}; border-radius: 8px; margin-top: 15px; padding-top: 20px; font-weight: bold; color: {c['accent']}; background-color: {c['group_bg']}; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 15px; padding: 0 5px 0 5px; }}
        QLineEdit, QComboBox {{ background-color: {c['input_bg']}; border: 1px solid {c['input_border']}; border-radius: 4px; padding: 6px; color: {c['fg']}; }}
        QLineEdit:focus, QComboBox:focus {{ border: 1px solid {c['focus']}; }}
        QPushButton {{ background-color: {c['btn_bg']}; border: 1px solid {c['btn_border']}; border-radius: 4px; padding: 8px 15px; font-weight: bold; color: {c['fg']}; }}
        QPushButton:hover {{ background-color: {c['btn_hover']}; }}
        QPushButton#btnSalvar {{ background-color: {c['btn_salvar']}; border: none; color: white; }}
        QPushButton#btnSalvar:hover {{ background-color: {c['btn_salvar_hover']}; }}
        QPushButton#btnExcluir {{ background-color: {c['btn_excluir']}; border: none; color: white; }}
        QPushButton#btnExcluir:hover {{ background-color: {c['btn_excluir_hover']}; }}
        QPushButton#btnPdf {{ background-color: {c['btn_pdf']}; border: none; color: white; }}
        QPushButton#btnPdf:hover {{ background-color: {c['btn_pdf_hover']}; }}
        QPushButton#btnEditarTabela {{ background-color: {c['btn_editar']}; border: none; padding: 4px; color: white; }}
        QTableWidget {{ background-color: {c['table_bg']}; border: 1px solid {c['grid']}; gridline-color: {c['grid']}; alternate-background-color: {c['table_alt']}; }}
        QTableWidget::item {{ padding: 5px; }}
        QTableWidget::item:selected {{ background-color: {c['focus']}; color: {c['row_sel_fg']}; }}
        QHeaderView::section {{ background-color: {c['header_bg']}; padding: 6px; border: none; border-right: 1px solid {c['grid']}; border-bottom: 1px solid {c['grid']}; font-weight: bold; color: {c['fg']}; }}
        QStatusBar {{ background-color: {c['status_bg']}; color: {c['status_fg']}; }}
        QMessageBox {{ background-color: {c['msg_bg']}; }}
    """

# ==========================================
# JANELA PRINCIPAL
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Cadastro de Clientes")
        self.setMinimumSize(1150, 800)

        self.settings = QSettings("MinhaEmpresa", "CadastroApp")
        self.tema_atual = self.settings.value("tema", "dark")
        self.id_editando = None

        geometria = self.settings.value("geometria")
        if geometria:
            self.restoreGeometry(geometria)

        self.setup_ui()
        self.configurar_atalhos()
        self.aplicar_estilos()
        self.carregar_dados()

    def closeEvent(self, event):
        self.settings.setValue("geometria", self.saveGeometry())
        self.settings.setValue("tema", self.tema_atual)
        super().closeEvent(event)

    def configurar_atalhos(self):
        atalhos = {
            "Ctrl+S": self.salvar_dados,
            "Ctrl+L": self.limpar_campos,
            "Ctrl+P": self.exportar_pdf,
            "Delete": self.excluir_dados,
            "F5": self.carregar_dados,
        }
        for tecla, funcao in atalhos.items():
            QShortcut(QKeySequence(tecla), self, funcao)

    # ==========================================
    # CONSTRUÇÃO DA INTERFACE
    # ==========================================
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Topo
        hbox_topo = QHBoxLayout()
        titulo = QLabel("Gestão de Clientes")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold;")
        hbox_topo.addWidget(titulo)
        hbox_topo.addStretch()

        self.btn_tema = QPushButton("☀️ Modo Claro" if self.tema_atual == "dark" else "🌙 Modo Escuro")
        self.btn_tema.setFixedWidth(140)
        self.btn_tema.clicked.connect(self.alternar_tema)
        hbox_topo.addWidget(self.btn_tema)
        layout.addLayout(hbox_topo)

        # Formulário
        group = QGroupBox("Dados do Cliente")
        grid = QGridLayout()
        grid.setSpacing(10)

        self.input_nome = QLineEdit(); self.input_nome.setPlaceholderText("Nome completo")
        self.input_cpf = QLineEdit(); self.input_cpf.setInputMask("999.999.999-99;_")
        self.input_email = QLineEdit(); self.input_email.setPlaceholderText("exemplo@email.com")
        self.input_celular = QLineEdit(); self.input_celular.setInputMask("(99) 99999-9999;_")
        self.input_cep = QLineEdit(); self.input_cep.setInputMask("99999-999;_")
        self.input_logradouro = QLineEdit()
        self.input_numero = QLineEdit()
        self.input_complemento = QLineEdit()
        self.input_bairro = QLineEdit()
        self.input_cidade = QLineEdit()

        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
                                    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
                                    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])

        self.btn_buscar_cep = QPushButton(" Buscar CEP")
        self.btn_buscar_cep.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.btn_buscar_cep.clicked.connect(self.buscar_cep)

        grid.addWidget(QLabel("Nome: *"), 0, 0); grid.addWidget(self.input_nome, 0, 1, 1, 3)
        grid.addWidget(QLabel("CPF: *"), 1, 0); grid.addWidget(self.input_cpf, 1, 1)
        grid.addWidget(QLabel("E-mail:"), 1, 2); grid.addWidget(self.input_email, 1, 3)
        grid.addWidget(QLabel("Celular:"), 2, 0); grid.addWidget(self.input_celular, 2, 1)
        grid.addWidget(QLabel("CEP:"), 2, 2)
        hbox_cep = QHBoxLayout()
        hbox_cep.addWidget(self.input_cep); hbox_cep.addWidget(self.btn_buscar_cep)
        grid.addLayout(hbox_cep, 2, 3)
        grid.addWidget(QLabel("Logradouro:"), 3, 0); grid.addWidget(self.input_logradouro, 3, 1, 1, 3)
        grid.addWidget(QLabel("Nº:"), 4, 0); grid.addWidget(self.input_numero, 4, 1)
        grid.addWidget(QLabel("Complemento:"), 4, 2); grid.addWidget(self.input_complemento, 4, 3)
        grid.addWidget(QLabel("Bairro:"), 5, 0); grid.addWidget(self.input_bairro, 5, 1, 1, 3)
        grid.addWidget(QLabel("Cidade:"), 6, 0); grid.addWidget(self.input_cidade, 6, 1)
        grid.addWidget(QLabel("Estado:"), 6, 2); grid.addWidget(self.combo_estado, 6, 3)

        group.setLayout(grid)
        layout.addWidget(group)

        # Campos que são limpos com frequência (facilita manutenção)
        self.campos_texto = [
            self.input_nome, self.input_cpf, self.input_email, self.input_celular,
            self.input_cep, self.input_logradouro, self.input_numero,
            self.input_complemento, self.input_bairro, self.input_cidade,
        ]

        # Botões CRUD
        hbox_btn = QHBoxLayout()
        self.btn_salvar = QPushButton(" Salvar"); self.btn_salvar.setObjectName("btnSalvar")
        self.btn_salvar.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.btn_limpar = QPushButton(" Limpar")
        self.btn_limpar.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        self.btn_excluir = QPushButton(" Excluir"); self.btn_excluir.setObjectName("btnExcluir")
        self.btn_excluir.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.btn_pdf = QPushButton(" Exportar PDF"); self.btn_pdf.setObjectName("btnPdf")
        self.btn_pdf.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))

        self.btn_salvar.clicked.connect(self.salvar_dados)
        self.btn_limpar.clicked.connect(self.limpar_campos)
        self.btn_excluir.clicked.connect(self.excluir_dados)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        for b in (self.btn_salvar, self.btn_limpar, self.btn_excluir):
            hbox_btn.addWidget(b)
        hbox_btn.addStretch()
        hbox_btn.addWidget(self.btn_pdf)
        layout.addLayout(hbox_btn)

        # Tabela e filtro
        group_lista = QGroupBox("Lista de Clientes")
        layout_lista = QVBoxLayout()

        hbox_pesq = QHBoxLayout()
        hbox_pesq.addWidget(QLabel("Filtrar por:"))
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(["Todos", "Nome", "CPF", "E-mail", "Cidade"])
        self.combo_filtro.setFixedWidth(110)
        self.input_pesquisa = QLineEdit()
        self.input_pesquisa.setPlaceholderText("🔍 Digite uma palavra para filtrar os dados da tabela...")
        self.input_pesquisa.textChanged.connect(self.filtrar_tabela)
        hbox_pesq.addWidget(self.combo_filtro)
        hbox_pesq.addWidget(self.input_pesquisa)
        layout_lista.addLayout(hbox_pesq)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(9)
        self.tabela.setHorizontalHeaderLabels(["ID", "Data", "Nome", "CPF", "E-mail", "Celular", "Cidade", "Estado", "Ações"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for col, largura in [(0, 50), (1, 110), (8, 90)]:
            self.tabela.setColumnWidth(col, largura)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.cellDoubleClicked.connect(self.on_double_click)
        layout_lista.addWidget(self.tabela)

        group_lista.setLayout(layout_lista)
        layout.addWidget(group_lista)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.lbl_contador = QLabel("Total: 0 clientes")
        self.status_bar.addPermanentWidget(self.lbl_contador)
        self.status_bar.showMessage("Pronto. Atalhos: Ctrl+S Salvar | Ctrl+P Exportar PDF | F5 Atualizar")

    # ==========================================
    # CRUD
    # ==========================================
    def validar_campos(self):
        for campo in (self.input_nome, self.input_cpf, self.input_email):
            campo.setStyleSheet("")

        nome = self.input_nome.text().strip()
        cpf = limpar_formatacao(self.input_cpf.text())
        email = self.input_email.text().strip()

        if not nome:
            self.input_nome.setStyleSheet("border: 1px solid red;")
            self.mostrar_erro("O campo Nome é obrigatório.")
            return False

        if not cpf or len(cpf) < 11 or not validar_cpf(cpf):
            self.input_cpf.setStyleSheet("border: 1px solid red;")
            self.mostrar_erro("CPF inválido ou incompleto.")
            return False

        if email and not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            self.input_email.setStyleSheet("border: 1px solid red;")
            self.mostrar_erro("O e-mail informado é inválido.")
            return False

        return True

    def verificar_duplicados(self, cpf, email):
        if self.id_editando:
            row = db_execute("SELECT id FROM pessoas WHERE cpf=? AND id!=?", (cpf, self.id_editando), "one")
        else:
            row = db_execute("SELECT id FROM pessoas WHERE cpf=?", (cpf,), "one")
        if row:
            return "CPF já cadastrado no sistema."

        if email:
            if self.id_editando:
                row = db_execute("SELECT id FROM pessoas WHERE email=? AND id!=?", (email, self.id_editando), "one")
            else:
                row = db_execute("SELECT id FROM pessoas WHERE email=?", (email,), "one")
            if row:
                return "E-mail já cadastrado no sistema."
        return None

    def salvar_dados(self):
        """CREATE e UPDATE."""
        if not self.validar_campos():
            return

        cpf = limpar_formatacao(self.input_cpf.text())
        email = self.input_email.text().strip()

        erro = self.verificar_duplicados(cpf, email)
        if erro:
            self.mostrar_erro(erro)
            return

        # Guarda informações antes de limpar os campos
        nome_cliente = self.input_nome.text().strip()
        modo_edicao = self.id_editando is not None

        dados = (
            nome_cliente, cpf, email,
            limpar_formatacao(self.input_celular.text()),
            limpar_formatacao(self.input_cep.text()),
            self.input_logradouro.text().strip(), self.input_numero.text().strip(),
            self.input_complemento.text().strip(), self.input_bairro.text().strip(),
            self.input_cidade.text().strip(), self.combo_estado.currentText()
        )

        try:
            if not modo_edicao:
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                db_execute('''
                    INSERT INTO pessoas
                    (nome, cpf, email, celular, cep, logradouro, numero, complemento, bairro, cidade, estado, data_cadastro)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', dados + (data_atual,))
                self.status_bar.showMessage("Cliente cadastrado com sucesso!", 5000)
            else:
                db_execute('''
                    UPDATE pessoas SET nome=?, cpf=?, email=?, celular=?, cep=?, logradouro=?,
                    numero=?, complemento=?, bairro=?, cidade=?, estado=? WHERE id=?
                ''', dados + (self.id_editando,))
                self.status_bar.showMessage("Cadastro atualizado com sucesso!", 5000)

            # Mensagem de sucesso personalizada
            msg = QMessageBox(self)
            msg.setWindowTitle("Sucesso")
            msg.setIcon(QMessageBox.Information)
            msg.setTextFormat(Qt.RichText)
            if not modo_edicao:
                msg.setText(
                    f"<h3>✅ Cliente cadastrado com sucesso!</h3>"
                    f"<p><b>Nome:</b> {nome_cliente}</p>"
                    f"<p><b>CPF:</b> {formatar_cpf(cpf)}</p>"
                    f"<p>O novo registro já está disponível na lista abaixo.</p>"
                )
            else:
                msg.setText(
                    f"<h3>✅ Cadastro atualizado com sucesso!</h3>"
                    f"<p><b>Nome:</b> {nome_cliente}</p>"
                    f"<p><b>CPF:</b> {formatar_cpf(cpf)}</p>"
                    f"<p>As alterações foram salvas no banco de dados.</p>"
                )
            msg.exec()

            self.limpar_campos()
            self.carregar_dados()
        except sqlite3.Error as e:
            self.mostrar_erro(f"Erro no banco de dados: {e}")

    def carregar_dados(self):
        """READ - lista todos os registros.
        
        A query SELECT usa a MESMA ordem dos cabeçalhos da tabela visual:
        [0] ID, [1] Data, [2] Nome, [3] CPF, [4] E-mail, [5] Celular, [6] Cidade, [7] Estado
        """
        self.tabela.setSortingEnabled(False)
        self.tabela.setRowCount(0)

        resultados = db_execute('''
            SELECT id, data_cadastro, nome, cpf, email, celular, cidade, estado
            FROM pessoas
            ORDER BY id DESC
        ''', fetch="all")

        for linha, dados in enumerate(resultados):
            self.tabela.insertRow(linha)

            dados_visuais = list(dados)
            dados_visuais[3] = formatar_cpf(dados_visuais[3])       # CPF
            dados_visuais[5] = formatar_celular(dados_visuais[5])   # Celular

            for coluna, valor in enumerate(dados_visuais):
                item = QTableWidgetItem(str(valor))
                if coluna in (0, 1, 7):  # ID, Data e Estado centralizados
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabela.setItem(linha, coluna, item)

            btn = QPushButton("Editar")
            btn.setObjectName("btnEditarTabela")
            btn.clicked.connect(lambda _, i=dados[0]: self.preparar_edicao(i))
            self.tabela.setCellWidget(linha, 8, btn)

        self.tabela.setSortingEnabled(True)
        self.atualizar_contador()

    def preparar_edicao(self, id_pessoa):
        """Prepara o formulário para edição (parte do UPDATE).
        
        Usa SELECT * porque precisamos de TODOS os campos para preencher o formulário.
        Ordem: [0]id [1]nome [2]cpf [3]email [4]celular [5]cep 
               [6]logradouro [7]numero [8]complemento [9]bairro 
               [10]cidade [11]estado [12]data_cadastro
        """
        dados = db_execute("SELECT * FROM pessoas WHERE id=?", (id_pessoa,), "one")
        if not dados:
            return

        self.id_editando = dados[0]
        self.input_nome.setText(dados[1])
        self.input_cpf.setText(dados[2])
        self.input_email.setText(dados[3])
        self.input_celular.setText(dados[4])
        self.input_cep.setText(dados[5])
        self.input_logradouro.setText(dados[6])
        self.input_numero.setText(dados[7])
        self.input_complemento.setText(dados[8])
        self.input_bairro.setText(dados[9])
        self.input_cidade.setText(dados[10])
        self.combo_estado.setCurrentText(dados[11])
        self.status_bar.showMessage(f"Editando registro ID {self.id_editando}...", 3000)
        self.input_nome.setFocus()

    def excluir_dados(self):
        """DELETE - remove o registro selecionado."""
        linha = self.tabela.currentRow()
        if linha == -1:
            self.mostrar_erro("Selecione um registro na tabela para excluir.")
            return

        id_pessoa = self.tabela.item(linha, 0).text()
        nome = self.tabela.item(linha, 2).text()

        if QMessageBox.question(self, "Confirmar Exclusão",
                                f"Deseja realmente excluir o cliente '{nome}'?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            db_execute("DELETE FROM pessoas WHERE id=?", (id_pessoa,))
            self.limpar_campos()
            self.carregar_dados()

            # Mensagem de confirmação de exclusão
            msg = QMessageBox(self)
            msg.setWindowTitle("Registro Excluído")
            msg.setIcon(QMessageBox.Information)
            msg.setTextFormat(Qt.RichText)
            msg.setText(
                f"<h3>🗑️ Registro excluído com sucesso!</h3>"
                f"<p>O cliente <b>{nome}</b> foi removido do sistema.</p>"
            )
            msg.exec()

            self.status_bar.showMessage("Registro excluído com sucesso!", 5000)

    # ==========================================
    # FILTRO
    # ==========================================
    def filtrar_tabela(self):
        texto = self.input_pesquisa.text().lower()
        filtro = self.combo_filtro.currentText()

        colunas = {
            "Todos": (2, 3, 4, 6),
            "Nome": (2,),
            "CPF": (3,),
            "E-mail": (4,),
            "Cidade": (6,),
        }.get(filtro, (2, 3, 4, 6))

        for linha in range(self.tabela.rowCount()):
            match = any(
                self.tabela.item(linha, col) and texto in self.tabela.item(linha, col).text().lower()
                for col in colunas
            )
            self.tabela.setRowHidden(linha, not match)

        self.atualizar_contador()

    def atualizar_contador(self):
        total = self.tabela.rowCount()
        visiveis = sum(1 for i in range(total) if not self.tabela.isRowHidden(i))
        self.lbl_contador.setText(f"Exibindo: {visiveis} / Total: {total}")

    # ==========================================
    # BUSCA DE CEP
    # ==========================================
    def buscar_cep(self):
        cep = limpar_formatacao(self.input_cep.text())
        if len(cep) != 8:
            self.mostrar_erro("CEP inválido. Digite os 8 números.")
            return

        self.status_bar.showMessage("Buscando CEP...")
        QApplication.processEvents()

        try:
            dados = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5).json()
            if "erro" in dados:
                self.mostrar_erro("CEP não encontrado.")
                return

            # Coleta os dados retornados
            logradouro = dados.get("logradouro", "")
            bairro = dados.get("bairro", "")
            cidade = dados.get("localidade", "")
            estado = dados.get("uf", "")

            # Preenche os campos
            self.input_logradouro.setText(logradouro)
            self.input_bairro.setText(bairro)
            self.input_cidade.setText(cidade)
            self.combo_estado.setCurrentText(estado)

            # Monta a lista de campos preenchidos (só mostra os que vieram com valor)
            campos_preenchidos = []
            if logradouro: campos_preenchidos.append(f"<b>Logradouro:</b> {logradouro}")
            if bairro:     campos_preenchidos.append(f"<b>Bairro:</b> {bairro}")
            if cidade:     campos_preenchidos.append(f"<b>Cidade:</b> {cidade}")
            if estado:     campos_preenchidos.append(f"<b>Estado:</b> {estado}")

            # Exibe a mensagem de sucesso
            msg = QMessageBox(self)
            msg.setWindowTitle("CEP Encontrado")
            msg.setIcon(QMessageBox.Information)
            msg.setTextFormat(Qt.RichText)
            msg.setText(
                f"<h3>✅ CEP {formatar_cep(cep)} encontrado!</h3>"
                f"<p>Os seguintes campos foram preenchidos automaticamente:</p>"
                f"<ul>{''.join(f'<li>{c}</li>' for c in campos_preenchidos)}</ul>"
                f"<p><i>Confira os dados e complete o número e o complemento.</i></p>"
            )
            msg.exec()

            self.status_bar.showMessage("CEP encontrado!", 3000)
            self.input_numero.setFocus()

        except requests.exceptions.RequestException:
            self.mostrar_erro("Falha de conexão. Verifique sua internet.")
        except Exception as e:
            self.mostrar_erro(f"Erro inesperado: {e}")

    # ==========================================
    # EXPORTAÇÃO PDF
    # ==========================================
    def exportar_pdf(self):
        if self.tabela.rowCount() == 0:
            self.mostrar_erro("Não há dados para exportar.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF",
            f"clientes_{datetime.now().strftime('%Y-%m-%d')}.pdf",
            "Arquivos PDF (*.pdf)"
        )
        if not filename:
            return

        try:
            doc = SimpleDocTemplate(filename, pagesize=landscape(A4),
                                    leftMargin=1*cm, rightMargin=1*cm,
                                    topMargin=1*cm, bottomMargin=1*cm)
            estilos = getSampleStyleSheet()
            titulo_style = ParagraphStyle('TituloCustom', parent=estilos['Title'],
                                          fontSize=16, textColor=colors.HexColor("#1a1a1a"),
                                          spaceAfter=6)

            cabecalhos = ["ID", "Data", "Nome", "CPF", "E-mail", "Celular", "Cidade", "Estado"]
            dados_tabela = [cabecalhos]

            # Adiciona apenas as linhas visíveis (respeita o filtro)
            for linha in range(self.tabela.rowCount()):
                if self.tabela.isRowHidden(linha):
                    continue
                dados_tabela.append([
                    self.tabela.item(linha, col).text() if self.tabela.item(linha, col) else ""
                    for col in range(8)
                ])

            tabela_pdf = Table(dados_tabela, repeatRows=1)
            tabela_pdf.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00bcd4")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))

            elementos = [
                Paragraph("Relatório de Clientes", titulo_style),
                Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", estilos['Normal']),
                Spacer(1, 0.5 * cm),
                tabela_pdf,
            ]
            doc.build(elementos)
            self.status_bar.showMessage(f"PDF exportado: {filename}", 5000)
            QMessageBox.information(self, "Sucesso", f"PDF gerado com sucesso em:\n{filename}")
        except Exception as e:
            self.mostrar_erro(f"Erro ao gerar PDF: {e}")

    # ==========================================
    # MÉTODOS AUXILIARES
    # ==========================================
    def on_double_click(self, row, column):
        if column == 8: return
        self.preparar_edicao(self.tabela.item(row, 0).text())

    def mostrar_erro(self, mensagem):
        QMessageBox.critical(self, "Erro", mensagem)
        self.status_bar.showMessage("Erro: " + mensagem, 5000)

    def limpar_campos(self):
        self.id_editando = None
        for campo in self.campos_texto:
            campo.clear()
        self.combo_estado.setCurrentIndex(0)
        for campo in (self.input_nome, self.input_cpf, self.input_email):
            campo.setStyleSheet("")
        self.status_bar.showMessage("Campos limpos.")
        self.input_nome.setFocus()

    def alternar_tema(self):
        self.tema_atual = "light" if self.tema_atual == "dark" else "dark"
        self.btn_tema.setText("🌙 Modo Escuro" if self.tema_atual == "light" else "☀️ Modo Claro")
        self.aplicar_estilos()

    def aplicar_estilos(self):
        self.setStyleSheet(montar_qss(CORES[self.tema_atual]))

# ==========================================
# PONTO DE ENTRADA
# ==========================================
if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    app.setOrganizationName("MinhaEmpresa")
    app.setApplicationName("CadastroApp")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())