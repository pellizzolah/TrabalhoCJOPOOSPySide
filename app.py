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
from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import QKeySequence, QShortcut

DB_PATH = "cadastro.db"
EMPRESA = "PellizzolaTechs"
APP = "CadastroApp"
POR_PAGINA = 50

ESTADOS = ["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT",
           "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO",
           "RR", "SC", "SP", "SE", "TO"]

FILTROS = {"Todos": "nome", "Nome": "nome", "CPF": "cpf",
           "E-mail": "email", "Cidade": "cidade"}

ATALHOS = {
    "Ctrl+S": "salvar_dados", "Ctrl+L": "limpar_campos",
    "Ctrl+P": "exportar_pdf", "Delete": "excluir_dados",
    "F5": "carregar_dados", "Ctrl+Shift+N": "nova_pagina",
    "Alt+Left": "pagina_anterior", "Alt+Right": "proxima_pagina",
}

CAMPOS_FORM = [
    (0, 0, 4, "Nome: *",     "nome",        {"placeholder": "Nome completo"}),
    (1, 0, 1, "CPF: *",      "cpf",         {"mask": "999.999.999-99;_"}),
    (1, 2, 1, "E-mail:",     "email",       {"placeholder": "exemplo@email.com"}),
    (2, 0, 1, "Celular:",    "celular",     {"mask": "(99) 99999-9999;_"}),
    (2, 2, 1, "CEP:",        "cep",         {"mask": "99999-999;_"}),
    (3, 0, 4, "Logradouro:", "logradouro",  {}),
    (4, 0, 1, "Nº:",         "numero",      {}),
    (4, 2, 1, "Complemento:","complemento", {}),
    (5, 0, 4, "Bairro:",     "bairro",      {}),
    (6, 0, 1, "Cidade:",     "cidade",      {}),
]

CAMPOS_DB = ["nome", "cpf", "email", "celular", "cep", "logradouro",
             "numero", "complemento", "bairro", "cidade"]

from reportlab.lib import colors as rl_colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

PDF_TABLE_STYLE = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor("#00bcd4")),
    ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [rl_colors.white, rl_colors.HexColor("#f0f0f0")]),
    ('GRID', (0, 0), (-1, -1), 0.5, rl_colors.grey),
    ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
])

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

QSS_TEMPLATE = """
QMainWindow, QWidget {{ background-color: {bg}; color: {fg}; font-family: 'Segoe UI', Arial; font-size: 14px; }}
QGroupBox {{ border: 1px solid {input_border}; border-radius: 8px; margin-top: 15px; padding-top: 20px; font-weight: bold; color: {accent}; background-color: {group_bg}; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 15px; padding: 0 5px 0 5px; }}
QLineEdit, QComboBox {{ background-color: {input_bg}; border: 1px solid {input_border}; border-radius: 4px; padding: 6px; color: {fg}; }}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {focus}; }}
QLineEdit[valido="true"] {{ border: 1px solid {btn_salvar}; }}
QLineEdit[invalido="true"] {{ border: 1px solid {btn_excluir}; }}
QPushButton {{ background-color: {btn_bg}; border: 1px solid {btn_border}; border-radius: 4px; padding: 8px 15px; font-weight: bold; color: {fg}; }}
QPushButton:hover {{ background-color: {btn_hover}; }}
QPushButton#btnSalvar {{ background-color: {btn_salvar}; border: none; color: white; }}
QPushButton#btnSalvar:hover {{ background-color: {btn_salvar_hover}; }}
QPushButton#btnExcluir {{ background-color: {btn_excluir}; border: none; color: white; }}
QPushButton#btnExcluir:hover {{ background-color: {btn_excluir_hover}; }}
QPushButton#btnPdf {{ background-color: {btn_pdf}; border: none; color: white; }}
QPushButton#btnPdf:hover {{ background-color: {btn_pdf_hover}; }}
QPushButton#btnEditarTabela {{ background-color: {btn_editar}; border: none; padding: 4px; color: white; }}
QPushButton#btnPagina {{ background-color: {btn_bg}; border: 1px solid {btn_border}; padding: 4px 10px; }}
QTableWidget {{ background-color: {table_bg}; border: 1px solid {grid}; gridline-color: {grid}; alternate-background-color: {table_alt}; }}
QTableWidget::item {{ padding: 5px; }}
QTableWidget::item:selected {{ background-color: {focus}; color: {row_sel_fg}; }}
QHeaderView::section {{ background-color: {header_bg}; padding: 6px; border: none; border-right: 1px solid {grid}; border-bottom: 1px solid {grid}; font-weight: bold; color: {fg}; }}
QStatusBar {{ background-color: {status_bg}; color: {status_fg}; }}
QMessageBox {{ background-color: {msg_bg}; }}
"""


def db_execute(query, params=(), fetch=None):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        if fetch == "one": return cur.fetchone()
        if fetch == "all": return cur.fetchall()
        conn.commit()


def init_db():
    db_execute('''CREATE TABLE IF NOT EXISTS pessoas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL, cpf TEXT UNIQUE, email TEXT, celular TEXT,
        cep TEXT, logradouro TEXT, numero TEXT, complemento TEXT,
        bairro TEXT, cidade TEXT, estado TEXT, data_cadastro TEXT)''')


def formatar_cpf(cpf):
    if not cpf: return ""
    cpf = str(cpf)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def formatar_celular(celular):
    if not celular: return ""
    celular = str(celular)
    return f"({celular[:2]}) {celular[2:7]}-{celular[7:]}"


def formatar_cep(cep):
    if not cep: return ""
    cep = str(cep)
    return f"{cep[:5]}-{cep[5:]}"


def limpar_formatacao(texto):
    return re.sub(r'\D', '', texto)


def validar_cpf(cpf):
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(cpf[j]) * ((i + 1) - j) for j in range(i))
        resto = (soma * 10) % 11
        if resto in (10, 11): resto = 0
        if resto != int(cpf[i]): return False
    return True


def validar_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Cadastro de Clientes")
        self.setMinimumSize(1150, 800)

        self.settings = QSettings(EMPRESA, APP)
        self.tema_atual = self.settings.value("tema", "dark")
        self.id_editando = None
        self.pagina_atual = 0
        self.total_registros = 0

        geometria = self.settings.value("geometria")
        if geometria: self.restoreGeometry(geometria)

        self.setup_ui()
        self.configurar_atalhos()
        self.configurar_validacao_tempo_real()
        self.configurar_auto_save()
        self.aplicar_estilos()
        self.recuperar_rascunho()
        self.carregar_dados()

    def closeEvent(self, event):
        self.settings.setValue("geometria", self.saveGeometry())
        self.settings.setValue("tema", self.tema_atual)
        super().closeEvent(event)

    # ---------- FACTORIES ----------
    def _input(self, placeholder=None, mask=None):
        w = QLineEdit()
        if mask: w.setInputMask(mask)
        if placeholder: w.setPlaceholderText(placeholder)
        return w

    def _btn(self, texto, icone=None, objeto=None, callback=None, width=None):
        b = QPushButton(texto)
        if icone: b.setIcon(self.style().standardIcon(icone))
        if objeto: b.setObjectName(objeto)
        if callback: b.clicked.connect(callback)
        if width: b.setFixedWidth(width)
        return b

    def _msg(self, titulo, html, icone=QMessageBox.Information):
        m = QMessageBox(self)
        m.setWindowTitle(titulo)
        m.setIcon(icone)
        m.setTextFormat(Qt.RichText)
        m.setText(html)
        m.exec()

    # ---------- SETUP ----------
    def configurar_atalhos(self):
        for tecla, metodo in ATALHOS.items():
            QShortcut(QKeySequence(tecla), self, getattr(self, metodo))

    def configurar_validacao_tempo_real(self):
        self.input_cpf.textChanged.connect(self.validar_cpf_tempo_real)
        self.input_email.textChanged.connect(self.validar_email_tempo_real)

    def configurar_auto_save(self):
        self.timer_rascunho = QTimer(self)
        self.timer_rascunho.setSingleShot(True)
        self.timer_rascunho.setInterval(1500)
        self.timer_rascunho.timeout.connect(self.salvar_rascunho)
        for campo in CAMPOS_DB:
            getattr(self, f"input_{campo}").textChanged.connect(
                lambda: self.timer_rascunho.start())

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        hbox_topo = QHBoxLayout()
        titulo = QLabel("Gestão de Clientes")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold;")
        hbox_topo.addWidget(titulo)
        hbox_topo.addStretch()

        self.btn_tema = self._btn(
            "☀️ Modo Claro" if self.tema_atual == "dark" else "🌙 Modo Escuro",
            callback=self.alternar_tema, width=140)
        hbox_topo.addWidget(self.btn_tema)
        layout.addLayout(hbox_topo)

        self.group_form = QGroupBox("Dados do Cliente")
        grid = QGridLayout()
        grid.setSpacing(10)

        for row, col, span, label, key, opts in CAMPOS_FORM:
            widget = self._input(**opts)
            setattr(self, f"input_{key}", widget)
            grid.addWidget(QLabel(label), row, col)
            grid.addWidget(widget, row, col + 1, 1, span)

        self.btn_buscar_cep = self._btn(" Buscar CEP", QStyle.SP_BrowserReload,
                                        callback=self.buscar_cep)
        hbox_cep = QHBoxLayout()
        hbox_cep.addWidget(self.input_cep)
        hbox_cep.addWidget(self.btn_buscar_cep)
        grid.addLayout(hbox_cep, 2, 3)

        self.combo_estado = QComboBox()
        self.combo_estado.addItems(ESTADOS)
        grid.addWidget(QLabel("Estado:"), 6, 2)
        grid.addWidget(self.combo_estado, 6, 3)

        self.group_form.setLayout(grid)
        layout.addWidget(self.group_form)

        self.campos_texto = [getattr(self, f"input_{k}") for k in CAMPOS_DB]

        hbox_btn = QHBoxLayout()
        self.btn_salvar = self._btn(" Salvar", QStyle.SP_DialogSaveButton, "btnSalvar", self.salvar_dados)
        self.btn_limpar = self._btn(" Limpar", QStyle.SP_DialogResetButton, callback=self.limpar_campos)
        self.btn_excluir = self._btn(" Excluir", QStyle.SP_TrashIcon, "btnExcluir", self.excluir_dados)
        self.btn_pdf = self._btn(" Exportar PDF", QStyle.SP_FileIcon, "btnPdf", self.exportar_pdf)

        for b in (self.btn_salvar, self.btn_limpar, self.btn_excluir):
            hbox_btn.addWidget(b)
        hbox_btn.addStretch()
        hbox_btn.addWidget(self.btn_pdf)
        layout.addLayout(hbox_btn)

        group_lista = QGroupBox("Lista de Clientes")
        layout_lista = QVBoxLayout()

        hbox_pesq = QHBoxLayout()
        hbox_pesq.addWidget(QLabel("Filtrar por:"))
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(list(FILTROS.keys()))
        self.combo_filtro.setFixedWidth(110)
        self.combo_filtro.currentTextChanged.connect(self.resetar_e_carregar)

        self.input_pesquisa = self._input(
            placeholder="🔍 Digite uma palavra para filtrar os dados da tabela...")
        self.input_pesquisa.textChanged.connect(self.resetar_e_carregar)

        hbox_pesq.addWidget(self.combo_filtro)
        hbox_pesq.addWidget(self.input_pesquisa)
        layout_lista.addLayout(hbox_pesq)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(9)
        self.tabela.setHorizontalHeaderLabels(
            ["ID", "Data", "Nome", "CPF", "E-mail", "Celular", "Cidade", "Estado", "Ações"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for col, largura in ((0, 50), (1, 110), (8, 90)):
            self.tabela.setColumnWidth(col, largura)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.cellDoubleClicked.connect(self.on_double_click)
        layout_lista.addWidget(self.tabela)

        hbox_pag = QHBoxLayout()
        hbox_pag.addStretch()
        self.btn_ant = self._btn("◀ Anterior", objeto="btnPagina",
                                 callback=self.pagina_anterior, width=110)
        self.lbl_pagina = QLabel("Página 1 / 1")
        self.lbl_pagina.setAlignment(Qt.AlignCenter)
        self.lbl_pagina.setFixedWidth(150)
        self.btn_prox = self._btn("Próxima ▶", objeto="btnPagina",
                                  callback=self.proxima_pagina, width=110)

        hbox_pag.addWidget(self.btn_ant)
        hbox_pag.addWidget(self.lbl_pagina)
        hbox_pag.addWidget(self.btn_prox)
        hbox_pag.addStretch()
        layout_lista.addLayout(hbox_pag)

        group_lista.setLayout(layout_lista)
        layout.addWidget(group_lista)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.lbl_contador = QLabel("Total: 0 clientes")
        self.status_bar.addPermanentWidget(self.lbl_contador)
        self.status_bar.showMessage("Pronto. Atalhos: Ctrl+S Salvar | Ctrl+P PDF | F5 Atualizar")

    # ---------- VALIDAÇÃO EM TEMPO REAL ----------
    def _set_estado(self, campo, valido=None):
        if valido is None:
            campo.setProperty("valido", False)
            campo.setProperty("invalido", False)
        else:
            campo.setProperty("valido", valido)
            campo.setProperty("invalido", not valido)
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def validar_cpf_tempo_real(self):
        cpf = limpar_formatacao(self.input_cpf.text())
        if not cpf or len(cpf) < 11:
            self._set_estado(self.input_cpf, None)
        else:
            self._set_estado(self.input_cpf, validar_cpf(cpf))

    def validar_email_tempo_real(self):
        email = self.input_email.text().strip()
        if not email:
            self._set_estado(self.input_email, None)
        else:
            self._set_estado(self.input_email, validar_email(email))

    # ---------- AUTO-SAVE DE RASCUNHO ----------
    def salvar_rascunho(self):
        if self.id_editando: return
        valores = [c.text() for c in self.campos_texto] + [self.combo_estado.currentText()]
        if not any(v.strip() for v in valores): return
        self.settings.setValue("rascunho", valores)

    def recuperar_rascunho(self):
        rascunho = self.settings.value("rascunho")
        if not rascunho: return
        try:
            for campo, valor in zip(self.campos_texto, rascunho[:10]):
                campo.setText(valor)
            self.combo_estado.setCurrentText(rascunho[10])
            self.status_bar.showMessage("Rascunho recuperado.", 4000)
        except Exception:
            pass

    def limpar_rascunho(self):
        self.settings.remove("rascunho")

    # ---------- CRUD ----------
    def _dados_formulario(self):
        return {
            "nome": self.input_nome.text().strip(),
            "cpf": limpar_formatacao(self.input_cpf.text()),
            "email": self.input_email.text().strip(),
            "celular": limpar_formatacao(self.input_celular.text()),
            "cep": limpar_formatacao(self.input_cep.text()),
            "logradouro": self.input_logradouro.text().strip(),
            "numero": self.input_numero.text().strip(),
            "complemento": self.input_complemento.text().strip(),
            "bairro": self.input_bairro.text().strip(),
            "cidade": self.input_cidade.text().strip(),
            "estado": self.combo_estado.currentText(),
        }

    def validar_campos(self, dados):
        if not dados["nome"]:
            return self.mostrar_erro("O campo Nome é obrigatório.")
        if len(dados["cpf"]) != 11 or not validar_cpf(dados["cpf"]):
            return self.mostrar_erro("CPF inválido ou incompleto.")
        if dados["email"] and not validar_email(dados["email"]):
            return self.mostrar_erro("O e-mail informado é inválido.")
        return True

    def verificar_duplicados(self, cpf, email):
        def existe(campo, valor):
            if self.id_editando:
                return db_execute(f"SELECT 1 FROM pessoas WHERE {campo}=? AND id!=?",
                                  (valor, self.id_editando), "one")
            return db_execute(f"SELECT 1 FROM pessoas WHERE {campo}=?", (valor,), "one")

        if existe("cpf", cpf): return "CPF já cadastrado no sistema."
        if email and existe("email", email): return "E-mail já cadastrado no sistema."
        return None

    def salvar_dados(self):
        dados = self._dados_formulario()

        if not self.validar_campos(dados): return

        erro = self.verificar_duplicados(dados["cpf"], dados["email"])
        if erro: return self.mostrar_erro(erro)

        editando = self.id_editando is not None

        valores = (
            dados["nome"], dados["cpf"], dados["email"], dados["celular"],
            dados["cep"], dados["logradouro"], dados["numero"],
            dados["complemento"], dados["bairro"], dados["cidade"], dados["estado"]
        )

        if not editando:
            sql = '''INSERT INTO pessoas
                (nome, cpf, email, celular, cep, logradouro, numero, complemento,
                 bairro, cidade, estado, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            params = valores + (datetime.now().strftime("%d/%m/%Y %H:%M"),)
            msg = "Cliente cadastrado com sucesso!"
            rodape = "O novo registro já está disponível na lista abaixo."
        else:
            sql = '''UPDATE pessoas SET nome=?, cpf=?, email=?, celular=?, cep=?,
                logradouro=?, numero=?, complemento=?, bairro=?, cidade=?, estado=?
                WHERE id=?'''
            params = valores + (self.id_editando,)
            msg = "Cadastro atualizado com sucesso!"
            rodape = "As alterações foram salvas no banco de dados."

        try:
            db_execute(sql, params)
            self.status_bar.showMessage(msg, 5000)
            self._msg("Sucesso",
                      f"<h3>✅ {msg}</h3>"
                      f"<p><b>Nome:</b> {dados['nome']}</p>"
                      f"<p><b>CPF:</b> {formatar_cpf(dados['cpf'])}</p>"
                      f"<p>{rodape}</p>")
            self.limpar_campos()
            self.carregar_dados()
        except sqlite3.Error as e:
            self.mostrar_erro(f"Erro no banco de dados: {e}")

    def carregar_dados(self):
        self.tabela.setSortingEnabled(False)
        self.tabela.setRowCount(0)

        filtro = self.combo_filtro.currentText()
        termo = self.input_pesquisa.text().strip()
        coluna = FILTROS.get(filtro, "nome")

        if filtro == "Todos" and termo:
            where = "WHERE nome LIKE ? OR cpf LIKE ? OR email LIKE ? OR cidade LIKE ?"
            like = f"%{termo}%"
            params_where = (like, like, like, like)
        elif termo:
            where = f"WHERE {coluna} LIKE ?"
            params_where = (f"%{termo}%",)
        else:
            where = ""
            params_where = ()

        self.total_registros = db_execute(
            f"SELECT COUNT(*) FROM pessoas {where}", params_where, "one")[0]

        offset = self.pagina_atual * POR_PAGINA
        resultados = db_execute(f'''
            SELECT id, data_cadastro, nome, cpf, email, celular, cidade, estado
            FROM pessoas {where} ORDER BY id DESC LIMIT ? OFFSET ?''',
            params_where + (POR_PAGINA, offset), fetch="all")

        for linha, dados in enumerate(resultados):
            self.tabela.insertRow(linha)
            visuais = list(dados)
            visuais[3] = formatar_cpf(visuais[3])
            visuais[5] = formatar_celular(visuais[5])

            for coluna_idx, valor in enumerate(visuais):
                item = QTableWidgetItem(str(valor))
                if coluna_idx in (0, 1, 7):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabela.setItem(linha, coluna_idx, item)

            btn = self._btn("Editar", objeto="btnEditarTabela",
                            callback=lambda _, i=dados[0]: self.preparar_edicao(i))
            self.tabela.setCellWidget(linha, 8, btn)

        self.tabela.setSortingEnabled(True)
        self.atualizar_contador()
        self.atualizar_paginacao()

    def preparar_edicao(self, id_pessoa):
        dados = db_execute("SELECT * FROM pessoas WHERE id=?", (id_pessoa,), "one")
        if not dados: return

        self.id_editando = dados[0]
        for campo, valor in zip(self.campos_texto, dados[1:11]):
            campo.setText(valor)
        self.combo_estado.setCurrentText(dados[11])

        self.status_bar.showMessage(f"Editando registro ID {self.id_editando}...", 3000)
        self.input_nome.setFocus()

    def excluir_dados(self):
        linha = self.tabela.currentRow()
        if linha == -1:
            return self.mostrar_erro("Selecione um registro na tabela para excluir.")

        id_pessoa = self.tabela.item(linha, 0).text()
        nome = self.tabela.item(linha, 2).text()

        if QMessageBox.question(self, "Confirmar Exclusão",
                f"Deseja realmente excluir o cliente '{nome}'?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            db_execute("DELETE FROM pessoas WHERE id=?", (id_pessoa,))
            self.limpar_campos()
            self.carregar_dados()
            self._msg("Registro Excluído",
                      f"<h3>🗑️ Registro excluído com sucesso!</h3>"
                      f"<p>O cliente <b>{nome}</b> foi removido do sistema.</p>")
            self.status_bar.showMessage("Registro excluído com sucesso!", 5000)

    # ---------- PAGINAÇÃO ----------
    def _total_paginas(self):
        return max(1, (self.total_registros + POR_PAGINA - 1) // POR_PAGINA)

    def atualizar_paginacao(self):
        total_paginas = self._total_paginas()
        self.lbl_pagina.setText(f"Página {self.pagina_atual + 1} / {total_paginas}")
        self.btn_ant.setEnabled(self.pagina_atual > 0)
        self.btn_prox.setEnabled(self.pagina_atual < total_paginas - 1)

    def resetar_e_carregar(self):
        self.pagina_atual = 0
        self.carregar_dados()

    def pagina_anterior(self):
        if self.pagina_atual > 0:
            self.pagina_atual -= 1
            self.carregar_dados()

    def proxima_pagina(self):
        if self.pagina_atual < self._total_paginas() - 1:
            self.pagina_atual += 1
            self.carregar_dados()

    def nova_pagina(self):
        self.resetar_e_carregar()

    def atualizar_contador(self):
        visiveis = self.tabela.rowCount()
        self.lbl_contador.setText(
            f"Exibindo: {visiveis} / Total filtrado: {self.total_registros}")

    # ---------- CEP ----------
    def buscar_cep(self):
        cep = limpar_formatacao(self.input_cep.text())
        if len(cep) != 8:
            return self.mostrar_erro("CEP inválido. Digite os 8 números.")

        self.status_bar.showMessage("Buscando CEP...")
        QApplication.processEvents()

        try:
            d = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5).json()
            if "erro" in d:
                return self.mostrar_erro("CEP não encontrado.")

            campos = {"Logradouro": d.get("logradouro", ""),
                      "Bairro":     d.get("bairro", ""),
                      "Cidade":     d.get("localidade", ""),
                      "Estado":     d.get("uf", "")}

            self.input_logradouro.setText(campos["Logradouro"])
            self.input_bairro.setText(campos["Bairro"])
            self.input_cidade.setText(campos["Cidade"])
            self.combo_estado.setCurrentText(campos["Estado"])

            itens = "".join(f"<li><b>{k}:</b> {v}</li>" for k, v in campos.items() if v)

            self._msg("CEP Encontrado",
                      f"<h3>✅ CEP {formatar_cep(cep)} encontrado!</h3>"
                      f"<p>Os seguintes campos foram preenchidos automaticamente:</p>"
                      f"<ul>{itens}</ul>"
                      f"<p><i>Confira os dados e complete o número e o complemento.</i></p>")

            self.status_bar.showMessage("CEP encontrado!", 3000)
            self.input_numero.setFocus()

        except requests.exceptions.RequestException:
            self.mostrar_erro("Falha de conexão. Verifique sua internet.")
        except Exception as e:
            self.mostrar_erro(f"Erro inesperado: {e}")

    # ---------- PDF ----------
    def exportar_pdf(self):
        if self.total_registros == 0:
            return self.mostrar_erro("Não há dados para exportar.")

        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF",
            f"clientes_{datetime.now().strftime('%Y-%m-%d')}.pdf",
            "Arquivos PDF (*.pdf)")
        if not filename: return

        try:
            doc = SimpleDocTemplate(filename, pagesize=landscape(A4),
                                    leftMargin=1*cm, rightMargin=1*cm,
                                    topMargin=1*cm, bottomMargin=1*cm)
            estilos = getSampleStyleSheet()
            titulo_style = ParagraphStyle('TituloCustom', parent=estilos['Title'],
                                          fontSize=16, textColor=rl_colors.HexColor("#1a1a1a"),
                                          spaceAfter=6)

            linhas = [["ID", "Data", "Nome", "CPF", "E-mail", "Celular", "Cidade", "Estado"]]
            linhas += [
                [self.tabela.item(l, c).text() if self.tabela.item(l, c) else "" for c in range(8)]
                for l in range(self.tabela.rowCount())
            ]

            tabela = Table(linhas, repeatRows=1)
            tabela.setStyle(PDF_TABLE_STYLE)

            doc.build([
                Paragraph("Relatório de Clientes", titulo_style),
                Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", estilos['Normal']),
                Paragraph(f"Registros: {len(linhas) - 1}", estilos['Normal']),
                Spacer(1, 0.5 * cm),
                tabela,
            ])

            self.status_bar.showMessage(f"PDF exportado: {filename}", 5000)
            self._msg("Sucesso", f"PDF gerado com sucesso em:<br/>{filename}")
        except Exception as e:
            self.mostrar_erro(f"Erro ao gerar PDF: {e}")

    # ---------- AUXILIARES ----------
    def on_double_click(self, row, column):
        if column != 8:
            self.preparar_edicao(self.tabela.item(row, 0).text())

    def mostrar_erro(self, msg):
        QMessageBox.critical(self, "Erro", msg)
        self.status_bar.showMessage("Erro: " + msg, 5000)
        return False

    def limpar_campos(self):
        self.id_editando = None
        self.limpar_rascunho()
        for campo in self.campos_texto:
            campo.clear()
            self._set_estado(campo, None)
        self.combo_estado.setCurrentIndex(0)
        self.status_bar.showMessage("Campos limpos.")
        self.input_nome.setFocus()

    def alternar_tema(self):
        self.tema_atual = "light" if self.tema_atual == "dark" else "dark"
        self.btn_tema.setText("🌙 Modo Escuro" if self.tema_atual == "light" else "☀️ Modo Claro")
        self.aplicar_estilos()

    def aplicar_estilos(self):
        self.setStyleSheet(QSS_TEMPLATE.format(**CORES[self.tema_atual]))


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    app.setOrganizationName(EMPRESA)
    app.setApplicationName(APP)
    MainWindow().show()
    sys.exit(app.exec())