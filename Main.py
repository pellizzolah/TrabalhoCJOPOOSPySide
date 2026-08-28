import sys, re, sqlite3, requests
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastro")
        self.setMinimumSize(800, 600)
        self.conn = sqlite3.connect("cadastros.db")
        self.criar_banco()
        self.editando = None

        # Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Formulário
        form = QGroupBox("Dados")
        grid = QGridLayout(form)

        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Nome completo")
        self.cpf_cnpj = QLineEdit()
        self.cpf_cnpj.setPlaceholderText("CPF ou CNPJ")
        self.email = QLineEdit()
        self.email.setPlaceholderText("E-mail")
        self.celular = QLineEdit()
        self.celular.setPlaceholderText("(00) 00000-0000")
        self.cep = QLineEdit()
        self.cep.setPlaceholderText("CEP")
        self.logradouro = QLineEdit()
        self.logradouro.setEnabled(False)
        self.logradouro.setStyleSheet("background-color: #e0e0e0;")
        self.numero = QLineEdit()
        self.numero.setPlaceholderText("Nº")
        self.complemento = QLineEdit()
        self.complemento.setPlaceholderText("Comp.")
        self.bairro = QLineEdit()
        self.bairro.setEnabled(False)
        self.bairro.setStyleSheet("background-color: #e0e0e0;")
        self.cidade = QLineEdit()
        self.cidade.setEnabled(False)
        self.cidade.setStyleSheet("background-color: #e0e0e0;")
        self.estado = QComboBox()
        self.estado.addItems(["", "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"])

        # Máscaras
        self.cpf_cnpj.textChanged.connect(lambda t: self.mascara_cpf_cnpj())
        self.celular.textChanged.connect(lambda t: self.mascara_celular())
        self.cep.textChanged.connect(lambda t: self.mascara_cep())

        # Botão CEP
        self.btn_cep = QPushButton("Buscar")
        self.btn_cep.clicked.connect(self.consultar_cep)

        # Grid
        grid.addWidget(QLabel("Nome:"), 0, 0)
        grid.addWidget(self.nome, 0, 1, 1, 3)
        grid.addWidget(QLabel("CPF/CNPJ:"), 1, 0)
        grid.addWidget(self.cpf_cnpj, 1, 1)
        grid.addWidget(QLabel("E-mail:"), 2, 0)
        grid.addWidget(self.email, 2, 1)
        grid.addWidget(QLabel("Celular:"), 3, 0)
        grid.addWidget(self.celular, 3, 1)
        grid.addWidget(QLabel("CEP:"), 4, 0)
        grid.addWidget(self.cep, 4, 1)
        grid.addWidget(self.btn_cep, 4, 2)
        grid.addWidget(QLabel("Logradouro:"), 5, 0)
        grid.addWidget(self.logradouro, 5, 1, 1, 3)
        grid.addWidget(QLabel("Nº:"), 6, 0)
        grid.addWidget(self.numero, 6, 1)
        grid.addWidget(QLabel("Complemento:"), 6, 2)
        grid.addWidget(self.complemento, 6, 3)
        grid.addWidget(QLabel("Bairro:"), 7, 0)
        grid.addWidget(self.bairro, 7, 1, 1, 3)
        grid.addWidget(QLabel("Cidade:"), 8, 0)
        grid.addWidget(self.cidade, 8, 1)
        grid.addWidget(QLabel("Estado:"), 8, 2)
        grid.addWidget(self.estado, 8, 3)
        layout.addWidget(form)

        # Botões
        botoes = QHBoxLayout()
        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.clicked.connect(self.salvar)
        self.btn_salvar.setStyleSheet("background: #4CAF50; color: white;")
        btn_limpar = QPushButton("Limpar")
        btn_limpar.clicked.connect(self.limpar)
        btn_excluir = QPushButton("Excluir")
        btn_excluir.clicked.connect(self.excluir)
        btn_excluir.setStyleSheet("background: #f44336; color: white;")
        botoes.addWidget(self.btn_salvar)
        botoes.addWidget(btn_limpar)
        botoes.addWidget(btn_excluir)
        botoes.addStretch()
        layout.addLayout(botoes)

        # Tabela
        tabela_group = QGroupBox("Lista")
        vbox = QVBoxLayout(tabela_group)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Pesquisar:"))
        self.pesquisa = QLineEdit()
        self.pesquisa.setPlaceholderText("Nome, CPF ou e-mail")
        self.pesquisa.textChanged.connect(lambda t: self.carregar_dados(t.strip()))
        hbox.addWidget(self.pesquisa)
        vbox.addLayout(hbox)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(8)
        self.tabela.setHorizontalHeaderLabels(["ID", "Nome", "CPF/CNPJ", "E-mail", "Celular", "Cidade", "Estado", ""])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        vbox.addWidget(self.tabela)
        layout.addWidget(tabela_group)

        self.carregar_dados()

    def criar_banco(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS cadastros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, cpf_cnpj TEXT, email TEXT, celular TEXT, cep TEXT,
            logradouro TEXT, numero TEXT, complemento TEXT,
            bairro TEXT, cidade TEXT, estado TEXT)""")
        self.conn.commit()

    def mascara_cpf_cnpj(self):
        t = re.sub(r'\D', '', self.cpf_cnpj.text())
        if len(t) <= 11:
            if len(t) > 3: t = t[:3]+'.'+t[3:]
            if len(t) > 7: t = t[:7]+'.'+t[7:]
            if len(t) > 11: t = t[:11]+'-'+t[11:]
        else:
            if len(t) > 2: t = t[:2]+'.'+t[2:]
            if len(t) > 6: t = t[:6]+'.'+t[6:]
            if len(t) > 10: t = t[:10]+'/'+t[10:]
            if len(t) > 15: t = t[:15]+'-'+t[15:]
        self.cpf_cnpj.blockSignals(True)
        self.cpf_cnpj.setText(t[:18])
        self.cpf_cnpj.blockSignals(False)

    def mascara_celular(self):
        t = re.sub(r'\D', '', self.celular.text())
        if len(t) > 2: t = '('+t[:2]+') '+t[2:]
        if len(t) > 10: t = t[:10]+'-'+t[10:]
        self.celular.blockSignals(True)
        self.celular.setText(t[:15])
        self.celular.blockSignals(False)

    def mascara_cep(self):
        t = re.sub(r'\D', '', self.cep.text())
        if len(t) > 5: t = t[:5]+'-'+t[5:]
        self.cep.blockSignals(True)
        self.cep.setText(t[:9])
        self.cep.blockSignals(False)

    def valida_cpf(self, c):
        c = re.sub(r'\D', '', c)
        if len(c) != 11 or c == c[0]*11: return False
        for i in range(9, 11):
            s = sum(int(c[j])*(i+1-j) for j in range(i))
            d = 11 - s % 11
            if d >= 10: d = 0
            if int(c[i]) != d: return False
        return True

    def valida_cnpj(self, c):
        c = re.sub(r'\D', '', c)
        if len(c) != 14 or c == c[0]*14: return False
        p = [5,4,3,2,9,8,7,6,5,4,3,2]
        s = sum(int(c[i])*p[i] for i in range(12))
        d1 = 0 if s % 11 < 2 else 11 - s % 11
        if int(c[12]) != d1: return False
        p = [6,5,4,3,2,9,8,7,6,5,4,3,2]
        s = sum(int(c[i])*p[i] for i in range(13))
        d2 = 0 if s % 11 < 2 else 11 - s % 11
        return int(c[13]) == d2

    def valida_email(self, e):
        return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', e) is not None

    def verificar_duplicidade(self):
        cpf = re.sub(r'\D', '', self.cpf_cnpj.text())
        email = self.email.text().strip().lower()
        
        if self.editando:
            # Na edição, verifica se existe outro registro com mesmo CPF ou email
            existe = self.conn.execute(
                "SELECT id FROM cadastros WHERE (cpf_cnpj=? OR email=?) AND id!=?", 
                (cpf, email, self.editando)
            ).fetchone()
        else:
            # No cadastro, verifica se já existe CPF ou email
            existe = self.conn.execute(
                "SELECT id FROM cadastros WHERE cpf_cnpj=? OR email=?", 
                (cpf, email)
            ).fetchone()
        
        if existe:
            # Descobre qual campo está duplicado
            if self.editando:
                duplicado = self.conn.execute(
                    "SELECT cpf_cnpj, email FROM cadastros WHERE id=?", 
                    (existe[0],)
                ).fetchone()
            else:
                duplicado = self.conn.execute(
                    "SELECT cpf_cnpj, email FROM cadastros WHERE id=?", 
                    (existe[0],)
                ).fetchone()
            
            if duplicado:
                if duplicado[0] == cpf:
                    return "CPF/CNPJ já cadastrado!"
                elif duplicado[1] == email:
                    return "E-mail já cadastrado!"
        
        return None

    def valida_tudo(self):
        erros = []
        if not self.nome.text().strip(): erros.append("Nome obrigatório")
        if not self.cpf_cnpj.text().strip(): erros.append("CPF/CNPJ obrigatório")
        if not self.email.text().strip(): erros.append("E-mail obrigatório")
        if not self.celular.text().strip(): erros.append("Celular obrigatório")
        if not self.cep.text().strip(): erros.append("CEP obrigatório")

        c = re.sub(r'\D', '', self.cpf_cnpj.text())
        if c:
            if len(c) == 11 and not self.valida_cpf(c): erros.append("CPF inválido")
            elif len(c) == 14 and not self.valida_cnpj(c): erros.append("CNPJ inválido")
            elif len(c) not in (11, 14): erros.append("CPF/CNPJ deve ter 11 ou 14 dígitos")

        if self.email.text() and not self.valida_email(self.email.text()):
            erros.append("E-mail inválido")
        if re.sub(r'\D', '', self.celular.text()) and len(re.sub(r'\D', '', self.celular.text())) != 11:
            erros.append("Celular deve ter 11 dígitos")
        if re.sub(r'\D', '', self.cep.text()) and len(re.sub(r'\D', '', self.cep.text())) != 8:
            erros.append("CEP deve ter 8 dígitos")
        
        return erros

    def consultar_cep(self):
        cep = re.sub(r'\D', '', self.cep.text())
        if len(cep) != 8:
            QMessageBox.warning(self, "CEP", "CEP inválido")
            return
        try:
            r = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
            if r.status_code == 200:
                d = r.json()
                if 'erro' in d:
                    QMessageBox.information(self, "CEP", "CEP não encontrado")
                    return
                self.logradouro.setText(d.get('logradouro', ''))
                self.bairro.setText(d.get('bairro', ''))
                self.cidade.setText(d.get('localidade', ''))
                uf = d.get('uf', '')
                idx = self.estado.findText(uf)
                if idx >= 0: self.estado.setCurrentIndex(idx)
            else:
                QMessageBox.critical(self, "Erro", "Falha na consulta")
        except:
            QMessageBox.critical(self, "Erro", "Erro de conexão")

    def carregar_dados(self, filtro=''):
        if filtro:
            f = f'%{filtro}%'
            dados = self.conn.execute("SELECT id,nome,cpf_cnpj,email,celular,cidade,estado FROM cadastros WHERE nome LIKE ? OR cpf_cnpj LIKE ? OR email LIKE ? ORDER BY id DESC", (f,f,f)).fetchall()
        else:
            dados = self.conn.execute("SELECT id,nome,cpf_cnpj,email,celular,cidade,estado FROM cadastros ORDER BY id DESC").fetchall()

        self.tabela.setRowCount(len(dados))
        for i, row in enumerate(dados):
            for j, val in enumerate(row):
                self.tabela.setItem(i, j, QTableWidgetItem(str(val)))
            btn = QPushButton("Editar")
            btn.clicked.connect(lambda ch, id=row[0]: self.editar(id))
            self.tabela.setCellWidget(i, 7, btn)

    def salvar(self):
        erros = self.valida_tudo()
        if erros:
            QMessageBox.critical(self, "Erros", "\n".join(erros))
            return
        
        # Verifica duplicidade antes de salvar
        duplicidade = self.verificar_duplicidade()
        if duplicidade:
            QMessageBox.critical(self, "Erro", duplicidade)
            return

        dados = (
            self.nome.text().strip(), self.cpf_cnpj.text().strip(), self.email.text().strip().lower(),
            self.celular.text().strip(), self.cep.text().strip(), self.logradouro.text().strip(),
            self.numero.text().strip(), self.complemento.text().strip(), self.bairro.text().strip(),
            self.cidade.text().strip(), self.estado.currentText()
        )

        if self.editando:
            self.conn.execute("""UPDATE cadastros SET nome=?,cpf_cnpj=?,email=?,celular=?,cep=?,
                                logradouro=?,numero=?,complemento=?,bairro=?,cidade=?,estado=? 
                                WHERE id=?""", (*dados, self.editando))
            self.conn.commit()
            QMessageBox.information(self, "Sucesso", "Registro atualizado!")
            self.editando = None
            self.btn_salvar.setText("Salvar")
        else:
            self.conn.execute("""INSERT INTO cadastros (nome,cpf_cnpj,email,celular,cep,logradouro,
                                numero,complemento,bairro,cidade,estado) VALUES (?,?,?,?,?,?,?,?,?,?,?)""", dados)
            self.conn.commit()
            QMessageBox.information(self, "Sucesso", "Cadastro realizado!")

        self.limpar()
        self.carregar_dados()

    def editar(self, id):
        dados = self.conn.execute("SELECT * FROM cadastros WHERE id=?", (id,)).fetchone()
        if not dados: return

        self.limpar()
        self.editando = id
        self.btn_salvar.setText("Atualizar")

        self.nome.setText(dados[1])
        self.cpf_cnpj.setText(dados[2])
        self.email.setText(dados[3])
        self.celular.setText(dados[4])
        self.cep.setText(dados[5])
        self.logradouro.setText(dados[6])
        self.numero.setText(dados[7])
        self.complemento.setText(dados[8])
        self.bairro.setText(dados[9])
        self.cidade.setText(dados[10])
        idx = self.estado.findText(dados[11])
        if idx >= 0: self.estado.setCurrentIndex(idx)

    def excluir(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Seleção", "Selecione um registro para excluir")
            return

        id = int(self.tabela.item(linha, 0).text())
        if QMessageBox.question(self, "Confirmar", f"Excluir ID {id}?", 
                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.conn.execute("DELETE FROM cadastros WHERE id=?", (id,))
            self.conn.commit()
            self.carregar_dados()
            QMessageBox.information(self, "Sucesso", "Registro excluído!")

    def limpar(self):
        for campo in [self.nome, self.cpf_cnpj, self.email, self.celular, self.cep,
                     self.logradouro, self.numero, self.complemento, self.bairro, self.cidade]:
            campo.clear()
        self.estado.setCurrentIndex(0)
        self.editando = None
        self.btn_salvar.setText("Salvar")

    def closeEvent(self, e):
        self.conn.close()
        e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())