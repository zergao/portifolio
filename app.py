import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, Response, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.utils import secure_filename
from functools import wraps
from dotenv import load_dotenv
from flask_wtf import CSRFProtect, FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf.csrf import CSRFError
from flask import jsonify

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Agora você pode acessar as variáveis de ambiente
# print(os.getenv("SECRET_KEY"))
# print(os.getenv("ADMIN_PASSWORD"))

# Configuração da aplicação Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['ADMIN_PASSWORD'] = os.getenv('ADMIN_PASSWORD')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/www/portfolio/instance/portfolio.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16 MB para uploads

# Inicializar o banco de dados
db = SQLAlchemy(app)

# Ativar proteção CSRF
csrf = CSRFProtect(app)

# Manipulador de erro CSRF
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('Ação não permitida. Recarregue a página e tente novamente.', 'danger')
    return redirect(url_for('login'))

# Formulário de Login usando Flask-WTF
class LoginForm(FlaskForm):
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Entrar')

# Função auxiliar para remover arquivo, se existir
def remover_arquivo(caminho):
    if caminho and os.path.exists(caminho):
        os.remove(caminho)
        

# Modelos
class Tipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    def __repr__(self):
        return f'<Tipo {self.nome}>'

class StatusProduto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    def __repr__(self):
        return f'<Status {self.nome}>'

class Designer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    def __repr__(self):
        return f'<Designer {self.nome}>'

class Equipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    def __repr__(self):
        return f'<Equipe {self.nome}>'

class Colecao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    def __repr__(self):
        return f'<Colecao {self.nome}>'

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    detalhamento_tecnico = db.Column(db.Text, nullable=True)
    royalties = db.Column(db.String(150), nullable=True)
    restricao_tecido = db.Column(db.String(150), nullable=True)
    marca_artsofas = db.Column(db.Boolean, default=False)
    materia_prima_terceirizada = db.Column(db.Boolean, default=False)
    insumos = db.relationship('ProdutoInsumo', backref='produto', lazy='joined')
    desenho_tecnico = db.Column(db.String(150), nullable=True)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipo.id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('status_produto.id'), nullable=False)
    designer_id = db.Column(db.Integer, db.ForeignKey('designer.id'), nullable=False)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipe.id'), nullable=False)
    colecao_id = db.Column(db.Integer, db.ForeignKey('colecao.id'), nullable=True)
    foto_tumblr = db.Column(db.String(150), nullable=True)
    foto_360 = db.Column(db.String(150), nullable=True)
    usar_360 = db.Column(db.Boolean, default=False)

    tipo = db.relationship('Tipo', backref='produtos')
    status = db.relationship('StatusProduto', backref='produtos')
    designer = db.relationship('Designer', backref='produtos')
    equipe = db.relationship('Equipe', backref='produtos')
    colecao = db.relationship('Colecao', backref='produtos')

    def __repr__(self):
        return f'<Produto {self.nome}>'

# Modelo para insumos (matéria prima terceirizada)
class ProdutoInsumo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    cod = db.Column(db.String(50), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    fornecedores = db.Column(db.String(150), nullable=True)
    quantidades = db.Column(db.String(50), nullable=True)
    valor = db.Column(db.String(50), nullable=True)
    arquivo_anexo = db.Column(db.String(150), nullable=True)


# Modelo para imagens adicionais (opcional)
class ProdutoImagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    produto = db.relationship('Produto', backref='imagens')

# Modelos para Tecidos e Acabamentos
class Tecido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cod = db.Column(db.String(50), nullable=False, unique=True)
    caracteristica = db.Column(db.String(150), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    cor = db.Column(db.String(50), nullable=True)
    composicao = db.Column(db.String(150), nullable=True)
    fornecedor = db.Column(db.String(150), nullable=True)
    custo = db.Column(db.Float, nullable=True)
    def __repr__(self):
        return f'<Tecido {self.cod}>'

class Acabamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cod = db.Column(db.String(50), nullable=False, unique=True)
    caracteristica = db.Column(db.String(150), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    cor = db.Column(db.String(50), nullable=True)
    fornecedor = db.Column(db.String(150), nullable=True)
    custo = db.Column(db.Float, nullable=True)
    def __repr__(self):
        return f'<Acabamento {self.cod}>'

# Decorador para exigir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            flash("Por favor, faça o login para acessar esta página.", "danger")
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

# Rotas de Login/Logout
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    session.pop('admin_authenticated', None)
    
    if form.validate_on_submit():
        senha = form.senha.data
        if senha and senha == app.config.get('ADMIN_PASSWORD'):
            session['admin_authenticated'] = True
            flash("Login efetuado com sucesso!", "success")
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            else:
                return redirect(url_for('configuracoes_page'))
        else:
            flash("Senha incorreta. Acesso negado.", "danger")
            
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('admin_authenticated', None)
    flash("Logout efetuado com sucesso.", "success")
    return redirect(url_for('login'))

# Rota raiz redireciona para a página de produtos
@app.route('/')
def home():
    return redirect(url_for('produtos'))

@app.route('/produtos')
def produtos():
    produtos = Produto.query.all()
    return render_template('produtos.html', produtos=produtos)
    
# Rota para buscar dados dinamicamente
@app.route('/get_options')
def get_options():
    filtro = request.args.get('filtro')
    options = []
    if filtro == 'designer':
        designers = Designer.query.all()
        options = [{'id': d.id, 'nome': d.nome} for d in designers]
    elif filtro == 'equipe':
        equipes = Equipe.query.all()
        options = [{'id': e.id, 'nome': e.nome} for e in equipes]
    elif filtro == 'tipo':
        tipos = Tipo.query.all()
        options = [{'id': t.id, 'nome': t.nome} for t in tipos]
    elif filtro == 'status':
        statuses = StatusProduto.query.all()
        options = [{'id': s.id, 'nome': s.nome} for s in statuses]
    elif filtro == 'colecao':
        colecoes = Colecao.query.all()
        options = [{'id': c.id, 'nome': c.nome} for c in colecoes]
    return jsonify(options)
    
@app.route('/pesquisar', methods=['GET', 'POST'])
def pesquisar():
    termo = request.args.get('termo', '')
    filtro = request.args.get('filtro', 'nome')

    print(f"Filtro: {filtro}, Termo: {termo}")

    designers = Designer.query.all()
    equipes = Equipe.query.all()
    tipos = Tipo.query.all()
    statuses = StatusProduto.query.all()
    colecoes = Colecao.query.all()
    marcas = ["artsofas", "pollus"]

    produtos_result = Produto.query  # Começa com uma consulta base

    if filtro == 'nome':
        if termo:
            produtos_result = produtos_result.filter(Produto.nome.contains(termo))
    elif filtro == 'tipo':
        if termo:
            try:
                tipo_id = int(termo)
                produtos_result = produtos_result.filter(Produto.tipo_id == tipo_id)
            except ValueError:
                flash("Erro: Tipo inválido.", "danger")
                produtos_result = Produto.query.filter(False)
    elif filtro == 'status':
        if termo:
            try:
                status_id = int(termo)
                produtos_result = produtos_result.filter(Produto.status_id == status_id)
            except ValueError:
                flash("Erro: Status inválido.", "danger")
                produtos_result = Produto.query.filter(False)
    elif filtro == 'designer':
        if termo:
            try:
                designer_id = int(termo)
                produtos_result = produtos_result.filter(Produto.designer_id == designer_id)
            except ValueError:
                flash("Erro: Designer inválido.", "danger")
                produtos_result = Produto.query.filter(False)
    elif filtro == 'equipe':
        if termo:
            try:
                equipe_id = int(termo)
                produtos_result = produtos_result.filter(Produto.equipe_id == equipe_id)
            except ValueError:
                flash("Erro: Equipe inválido.", "danger")
                produtos_result = Produto.query.filter(False)
    elif filtro == 'colecao':
        if termo:
            try:
                colecao_id = int(termo)
                produtos_result = produtos_result.filter(Produto.colecao_id == colecao_id)
            except ValueError:
                flash("Erro: Coleção inválido.", "danger")
                produtos_result = Produto.query.filter(False)
        else:
             produtos_result = Produto.query
    elif filtro == 'empresa':
     if termo in marcas:
        produtos_result = produtos_result.filter(Produto.marca_artsofas == (termo == 'artsofas'))
     else:
        produtos_result = Produto.query.filter(False) #Filtra para não trazer nada
    else:
        produtos_result = Produto.query #Não passa nada

    produtos_result = produtos_result.all()  # Executa a consulta

    return render_template('produtos.html', produtos=produtos_result, filtro=filtro, termo=termo,
                           designers=designers, equipes=equipes, tipos=tipos, statuses=statuses, colecoes=colecoes)


# Rotas para pesquisa de Tecidos
@app.route('/pesquisar_tecidos', methods=['GET'])
@login_required
def pesquisar_tecidos():
    termo = request.args.get('termo', '')
    filtro = request.args.get('filtro', 'cod')
    if filtro == 'cod':
        tecidos_result = Tecido.query.filter(Tecido.cod.contains(termo)).all()
    elif filtro == 'caracteristica':
        tecidos_result = Tecido.query.filter(Tecido.caracteristica.contains(termo)).all()
    elif filtro == 'cor':
        tecidos_result = Tecido.query.filter(Tecido.cor.contains(termo)).all()
    elif filtro == 'fornecedor':
        tecidos_result = Tecido.query.filter(Tecido.fornecedor.contains(termo)).all()
    else:
        tecidos_result = Tecido.query.all()
    return render_template('tecidos.html', tecidos=tecidos_result, filtro=filtro, termo=termo)

# Rotas para pesquisa de Acabamentos
@app.route('/pesquisar_acabamentos', methods=['GET'])
@login_required
def pesquisar_acabamentos():
    termo = request.args.get('termo', '')
    filtro = request.args.get('filtro', 'cod')
    if filtro == 'cod':
        acabamentos_result = Acabamento.query.filter(Acabamento.cod.contains(termo)).all()
    elif filtro == 'caracteristica':
        acabamentos_result = Acabamento.query.filter(Acabamento.caracteristica.contains(termo)).all()
    elif filtro == 'cor':
        acabamentos_result = Acabamento.query.filter(Acabamento.cor.contains(termo)).all()
    elif filtro == 'fornecedor':
        acabamentos_result = Acabamento.query.filter(Acabamento.fornecedor.contains(termo)).all()
    else:
        acabamentos_result = Acabamento.query.all()
    return render_template('acabamentos.html', acabamentos=acabamentos_result, filtro=filtro, termo=termo)

@app.route('/produto/<int:produto_id>', methods=['GET'])

def produto(produto_id):
    # Obtém o produto e os insumos
    produto_item = Produto.query.get_or_404(produto_id)
    insumos = ProdutoInsumo.query.filter_by(produto_id=produto_id).all()

    # Renderiza o template do produto
    return render_template('produto.html', produto=produto_item, insumos=insumos)
    

# Rotas para Produtos
@app.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    try:
        if request.method == 'POST':
            # Coleta de dados do formulário
            nome = request.form['nome']
            descricao = request.form['descricao']
            detalhamento_tecnico = request.form.get('detalhamento_tecnico')
            royalties = request.form.get('royalties')
            restricao_tecido = request.form.get('restricao_tecido')
            tipo_id = request.form['tipo']
            status_id = request.form['status']
            designer_id = request.form['designer']
            equipe_id = request.form['equipe']
            colecao_id = request.form.get('colecao')
            
            # Checkboxes
            marca_artsofas = request.form.get('marca_artsofas') == 'on'
            materia_prima_terceirizada = request.form.get('materia_prima_terceirizada') == 'on'
            usar_360 = request.form.get('usar_360') == 'on'
            
            # Uploads de arquivos (desenho técnico, fotos)
            desenho_tecnico = handle_file_upload(request.files.get('desenho_tecnico'))
            filename_tumblr = handle_file_upload(request.files.get('foto_tumblr'))
            filename_360 = handle_file_upload(request.files.get('foto_360'))
            
            # Get desenho_tecnico_links
            desenho_tecnico_links = request.form.get('desenho_tecnico_links')
            
            # Criação do produto
            novo_produto = Produto(
                nome=nome,
                descricao=descricao,
                detalhamento_tecnico=detalhamento_tecnico,
                royalties=royalties,
                restricao_tecido=restricao_tecido,
                tipo_id=tipo_id,
                status_id=status_id,
                designer_id=designer_id,
                equipe_id=equipe_id,
                colecao_id=colecao_id if colecao_id else None,
                foto_tumblr=filename_tumblr,
                foto_360=filename_360,
                usar_360=usar_360,
                marca_artsofas=marca_artsofas,
                materia_prima_terceirizada=materia_prima_terceirizada,
                desenho_tecnico=desenho_tecnico_links # Salva os links no campo desenho_tecnico
            )
            db.session.add(novo_produto)
            db.session.commit()
            
            # Processamento dos insumos terceirizados
            if materia_prima_terceirizada:
                processar_insumos(request, novo_produto.id)

            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('produtos'))
        
        # Carregamento de dados para o formulário
        tipos = Tipo.query.all()
        statuses = StatusProduto.query.all()
        designers = Designer.query.all()
        equipes = Equipe.query.all()
        colecoes = Colecao.query.all()

        return render_template('cadastro.html', tipos=tipos, statuses=statuses,
                               designers=designers, equipes=equipes, colecoes=colecoes)
    
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao cadastrar produto: {str(e)}", 'danger')
        return redirect(url_for('cadastrar_produto'))

# Função auxiliar para upload de arquivos
def handle_file_upload(file):
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return filename
    return None

# Função auxiliar para processar insumos terceirizados
def processar_insumos(request, produto_id):
    insumo_cod_list = request.form.getlist('insumo_cod[]')
    insumo_descricao_list = request.form.getlist('insumo_descricao[]')
    insumo_fornecedores_list = request.form.getlist('insumo_fornecedores[]')
    insumo_quantidades_list = request.form.getlist('insumo_quantidades[]')
    insumo_valor_list = request.form.getlist('insumo_valor[]')
    insumo_arquivo_list = request.files.getlist('insumo_arquivo[]')

    for cod, desc, fornec, quant, valor, arquivo in zip(
            insumo_cod_list, insumo_descricao_list,
            insumo_fornecedores_list, insumo_quantidades_list,
            insumo_valor_list, insumo_arquivo_list):

        arquivo_nome = handle_file_upload(arquivo)

        novo_insumo = ProdutoInsumo(
            produto_id=produto_id,
            cod=cod,
            descricao=desc,
            fornecedores=fornec,
            quantidades=quant,
            valor=valor,
            arquivo_anexo=arquivo_nome
        )
        db.session.add(novo_insumo)
    db.session.commit()

def handle_file_upload(file):
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return filename
    return None

@app.route('/editar/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def editar(produto_id):
    produto_item = Produto.query.get_or_404(produto_id)
    
    if request.method == 'POST':
        # Atualiza os dados principais do produto
        produto_item.nome = request.form['nome']
        produto_item.descricao = request.form['descricao']
        produto_item.detalhamento_tecnico = request.form.get('detalhamento_tecnico')
        produto_item.royalties = request.form.get('royalties')
        produto_item.restricao_tecido = request.form.get('restricao_tecido')
        produto_item.tipo_id = request.form['tipo']
        produto_item.status_id = request.form['status']
        produto_item.designer_id = request.form['designer']
        produto_item.equipe_id = request.form['equipe']
        produto_item.colecao_id = request.form.get('colecao') if request.form.get('colecao') else None
        produto_item.marca_artsofas = request.form.get('marca_artsofas') == 'on'
        produto_item.materia_prima_terceirizada = request.form.get('materia_prima_terceirizada') == 'on'
        # Get desenho_tecnico_links
        produto_item.desenho_tecnico = request.form.get('desenho_tecnico_links') # Atualiza o campo com os links

        # Insumos Terceirizados
        insumo_cod_list = request.form.getlist('insumo_cod[]')
        insumo_descricao_list = request.form.getlist('insumo_descricao[]')
        insumo_fornecedores_list = request.form.getlist('insumo_fornecedores[]')
        insumo_quantidades_list = request.form.getlist('insumo_quantidades[]')
        insumo_valor_list = request.form.getlist('insumo_valor[]')
        insumo_arquivo_list = request.files.getlist('insumo_arquivo[]')
        insumos_remover_anexo = request.form.getlist('remover_anexo[]')
        insumos_remover = request.form.getlist('remover_insumo[]')  # Lista de insumos a serem removidos
        
        # Remover os insumos marcados para exclusão
        for insumo_id in insumos_remover:
            insumo = ProdutoInsumo.query.get(insumo_id)
            if insumo:
                # Remover arquivo se houver
                if insumo.arquivo_anexo:
                    remover_arquivo(os.path.join(app.config['UPLOAD_FOLDER'], insumo.arquivo_anexo))
                db.session.delete(insumo)

        # Atualiza insumos existentes e adiciona novos insumos
        for i, (cod, desc, fornec, quant, valor, arquivo) in enumerate(zip(
                insumo_cod_list, insumo_descricao_list, 
                insumo_fornecedores_list, insumo_quantidades_list, 
                insumo_valor_list, insumo_arquivo_list)):

            # Se o insumo já existe, atualiza os campos
            if i < len(produto_item.insumos):
                insumo = produto_item.insumos[i]
                insumo.cod = cod
                insumo.descricao = desc
                insumo.fornecedores = fornec
                insumo.quantidades = quant
                insumo.valor = valor

                # Remover anexo se marcado
                if str(insumo.id) in insumos_remover_anexo and insumo.arquivo_anexo:
                    remover_arquivo(os.path.join(app.config['UPLOAD_FOLDER'], insumo.arquivo_anexo))
                    insumo.arquivo_anexo = None

                # Adicionar novo anexo se fornecido
                if arquivo and arquivo.filename:
                    insumo.arquivo_anexo = handle_file_upload(arquivo)

            # Se o insumo não existe, cria um novo insumo
            else:
                novo_insumo = ProdutoInsumo(
                    produto_id=produto_item.id,
                    cod=cod,
                    descricao=desc,
                    fornecedores=fornec,
                    quantidades=quant,
                    valor=valor,
                    arquivo_anexo=handle_file_upload(arquivo) if arquivo and arquivo.filename else None
                )
                db.session.add(novo_insumo)

        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('produto', produto_id=produto_item.id))
    
    # Garante que os dados para os selects sejam carregados corretamente
    tipos = Tipo.query.all()
    statuses = StatusProduto.query.all()
    designers = Designer.query.all()
    equipes = Equipe.query.all()
    colecoes = Colecao.query.all()

    return render_template('editar.html', produto=produto_item, tipos=tipos,
                           statuses=statuses, designers=designers, 
                           equipes=equipes, colecoes=colecoes)


@app.route('/excluir_produto/<int:produto_id>')
@login_required
def excluir_produto(produto_id):
    produto_item = Produto.query.get_or_404(produto_id)
    # Remove arquivos (foto e desenho técnico)
    if produto_item.foto_tumblr:
        caminho_tumblr = os.path.join(app.config['UPLOAD_FOLDER'], produto_item.foto_tumblr)
        remover_arquivo(caminho_tumblr)
    if produto_item.foto_360:
        caminho_360 = os.path.join(app.config['UPLOAD_FOLDER'], produto_item.foto_360)
        remover_arquivo(caminho_360)
    if produto_item.desenho_tecnico:
        caminho_desenho = os.path.join(app.config['UPLOAD_FOLDER'], produto_item.desenho_tecnico)
        remover_arquivo(caminho_desenho)
    # Exclui os insumos associados
    for insumo in produto_item.insumos:
        db.session.delete(insumo)
    db.session.delete(produto_item)
    db.session.commit()
    flash('Produto e arquivos associados excluídos com sucesso!', 'success')
    return redirect(url_for('configuracoes_page') + "#produtos_config")
    
@app.route('/excluir_insumo/<int:produto_id>/<int:insumo_id>', methods=['GET'])
@login_required
def excluir_insumo(produto_id, insumo_id):
    # Encontra o produto e o insumo
    produto = Produto.query.get_or_404(produto_id)
    insumo = ProdutoInsumo.query.get_or_404(insumo_id)

    # Verifica se o insumo pertence ao produto
    if insumo.produto_id != produto.id:
        flash('Insumo não pertence a este produto!', 'danger')
        return redirect(url_for('produto', produto_id=produto.id))

    # Remove o arquivo anexado ao insumo, se existir
    if insumo.arquivo_anexo:
        caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], insumo.arquivo_anexo)
        if os.path.exists(caminho_arquivo):  # Garante que o arquivo existe antes de tentar removê-lo
            try:
                os.remove(caminho_arquivo)
                print(f"Arquivo {caminho_arquivo} removido com sucesso.")
            except Exception as e:
                flash(f"Erro ao remover o arquivo: {str(e)}", 'danger')
                return redirect(url_for('produto', produto_id=produto.id))

    # Remove o insumo do banco de dados
    db.session.delete(insumo)
    db.session.commit()

    # Exibe mensagem de sucesso
    flash('Insumo excluído com sucesso!', 'success')

    # Redireciona para a página de visualização do produto
    return redirect(url_for('produto', produto_id=produto.id))
    

# Rotas para Configurações (integrando cadastros e Dashboard)
@app.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes_page():
    active_tab = ""
    if request.method == 'POST':
        if 'novo_tipo' in request.form:
            nome_tipo = request.form['novo_tipo']
            novo_tipo = Tipo(nome=nome_tipo)
            db.session.add(novo_tipo)
            db.session.commit()
            flash('Tipo adicionado com sucesso!', 'success')
            active_tab = "tipos"
        elif 'novo_status' in request.form:
            nome_status = request.form['novo_status']
            novo_status = StatusProduto(nome=nome_status)
            db.session.add(novo_status)
            db.session.commit()
            flash('Status adicionado com sucesso!', 'success')
            active_tab = "status"
        elif 'novo_designer' in request.form:
            nome_designer = request.form['novo_designer']
            novo_designer = Designer(nome=nome_designer)
            db.session.add(novo_designer)
            db.session.commit()
            flash('Designer adicionado com sucesso!', 'success')
            active_tab = "designers"
        elif 'novo_equipe' in request.form:
            nome_equipe = request.form['novo_equipe']
            novo_equipe = Equipe(nome=nome_equipe)
            db.session.add(novo_equipe)
            db.session.commit()
            flash('Equipe adicionada com sucesso!', 'success')
            active_tab = "equipes"
        elif 'novo_colecao' in request.form:
            nome_colecao = request.form['novo_colecao']
            nova_colecao = Colecao(nome=nome_colecao)
            db.session.add(nova_colecao)
            db.session.commit()
            flash('Coleção adicionada com sucesso!', 'success')
            active_tab = "colecoes"
        return redirect(url_for('configuracoes_page') + "#" + active_tab)
    tipos = Tipo.query.all()
    statuses = StatusProduto.query.all()
    designers = Designer.query.all()
    equipes = Equipe.query.all()
    produtos = Produto.query.all()
    colecoes = Colecao.query.all()
    tecidos_list = Tecido.query.all()
    acabamentos_list = Acabamento.query.all()
    # Dashboard integrado
    designer_counts = db.session.query(Designer, func.count(Produto.id))\
        .join(Produto, Designer.id == Produto.designer_id)\
        .group_by(Designer.id).all()
    equipe_counts = db.session.query(Equipe, func.count(Produto.id))\
        .join(Produto, Equipe.id == Produto.equipe_id)\
        .group_by(Equipe.id).all()
    colecao_counts = db.session.query(Colecao, func.count(Produto.id))\
        .outerjoin(Produto, Colecao.id == Produto.colecao_id)\
        .group_by(Colecao.id).all()
    return render_template('configuracoes.html', tipos=tipos, statuses=statuses,
                           designers=designers, equipes=equipes, produtos=produtos,
                           colecoes=colecoes, tecidos=tecidos_list, acabamentos=acabamentos_list,
                           designer_counts=designer_counts, equipe_counts=equipe_counts, colecao_counts=colecao_counts)

# Rotas para editar e excluir entidades (Tipos, Status, Designer, Equipe, Coleção)
@app.route('/editar_tipo/<int:tipo_id>', methods=['GET', 'POST'])
@login_required
def editar_tipo(tipo_id):
    tipo = Tipo.query.get_or_404(tipo_id)
    if request.method == 'POST':
        tipo.nome = request.form['nome']
        db.session.commit()
        flash('Tipo atualizado com sucesso!', 'success')
        return redirect(url_for('configuracoes_page') + "#tipos")
    return render_template('editar_tipo.html', tipo=tipo)

@app.route('/excluir_tipo/<int:tipo_id>')
@login_required
def excluir_tipo(tipo_id):
    tipo = Tipo.query.get_or_404(tipo_id)
    produtos_associados = Produto.query.filter_by(tipo_id=tipo.id).count()
    if produtos_associados > 0:
        flash(f"Não é possível excluir o tipo '{tipo.nome}', pois existem {produtos_associados} produtos associados.", "danger")
        return redirect(url_for('configuracoes_page') + "#tipos")
    db.session.delete(tipo)
    db.session.commit()
    flash("Tipo excluído com sucesso!", "success")
    return redirect(url_for('configuracoes_page') + "#tipos")

@app.route('/editar_status/<int:status_id>', methods=['GET', 'POST'])
@login_required
def editar_status(status_id):
    status = StatusProduto.query.get_or_404(status_id)
    if request.method == 'POST':
        status.nome = request.form['nome']
        db.session.commit()
        flash('Status atualizado com sucesso!', 'success')
        return redirect(url_for('configuracoes_page') + "#status")
    return render_template('editar_status.html', status=status)

@app.route('/excluir_status/<int:status_id>')
@login_required
def excluir_status(status_id):
    status = StatusProduto.query.get_or_404(status_id)
    produtos_associados = Produto.query.filter_by(status_id=status.id).count()
    if produtos_associados > 0:
        flash(f"Não é possível excluir o status '{status.nome}', pois existem {produtos_associados} produtos associados.", "danger")
        return redirect(url_for('configuracoes_page') + "#status")
    db.session.delete(status)
    db.session.commit()
    flash("Status excluído com sucesso!", "success")
    return redirect(url_for('configuracoes_page') + "#status")

@app.route('/editar_designer/<int:designer_id>', methods=['GET', 'POST'])
@login_required
def editar_designer(designer_id):
    designer = Designer.query.get_or_404(designer_id)
    if request.method == 'POST':
        designer.nome = request.form['nome']
        db.session.commit()
        flash('Designer atualizado com sucesso!', 'success')
        return redirect(url_for('configuracoes_page') + "#designers")
    return render_template('editar_designer.html', designer=designer)

@app.route('/excluir_designer/<int:designer_id>')
@login_required
def excluir_designer(designer_id):
    designer = Designer.query.get_or_404(designer_id)
    produtos_associados = Produto.query.filter_by(designer_id=designer.id).count()
    if produtos_associados > 0:
        flash(f"Não é possível excluir o designer '{designer.nome}', pois existem {produtos_associados} produtos associados.", "danger")
        return redirect(url_for('configuracoes_page') + "#designers")
    db.session.delete(designer)
    db.session.commit()
    flash("Designer excluído com sucesso!", "success")
    return redirect(url_for('configuracoes_page') + "#designers")

@app.route('/editar_equipe/<int:equipe_id>', methods=['GET', 'POST'])
@login_required
def editar_equipe(equipe_id):
    equipe = Equipe.query.get_or_404(equipe_id)
    if request.method == 'POST':
        equipe.nome = request.form['nome']
        db.session.commit()
        flash('Equipe atualizada com sucesso!', 'success')
        return redirect(url_for('configuracoes_page') + "#equipes")
    return render_template('editar_equipe.html', equipe=equipe)

@app.route('/excluir_equipe/<int:equipe_id>')
@login_required
def excluir_equipe(equipe_id):
    equipe = Equipe.query.get_or_404(equipe_id)
    produtos_associados = Produto.query.filter_by(equipe_id=equipe.id).count()
    if produtos_associados > 0:
        flash(f"Não é possível excluir a equipe '{equipe.nome}', pois existem {produtos_associados} produtos associados.", "danger")
        return redirect(url_for('configuracoes_page') + "#equipes")
    db.session.delete(equipe)
    db.session.commit()
    flash("Equipe excluída com sucesso!", "success")
    return redirect(url_for('configuracoes_page') + "#equipes")

@app.route('/editar_colecao/<int:colecao_id>', methods=['GET', 'POST'])
@login_required
def editar_colecao(colecao_id):
    colecao = Colecao.query.get_or_404(colecao_id)
    if request.method == 'POST':
        colecao.nome = request.form['nome']
        db.session.commit()
        flash('Coleção atualizada com sucesso!', 'success')
        return redirect(url_for('configuracoes_page') + "#colecoes")
    return render_template('editar_colecao.html', colecao=colecao)

@app.route('/excluir_colecao/<int:colecao_id>')
@login_required
def excluir_colecao(colecao_id):
    colecao = Colecao.query.get_or_404(colecao_id)
    db.session.delete(colecao)
    db.session.commit()
    flash('Coleção excluída com sucesso!', 'success')
    return redirect(url_for('configuracoes_page') + "#colecoes")

# Rotas para Tecidos
@app.route('/tecidos', methods=['GET', 'POST'])
def tecidos():
    if request.method == 'POST':
        cod = request.form.get('cod')
        caracteristica = request.form.get('caracteristica')
        descricao = request.form.get('descricao')
        cor = request.form.get('cor')
        composicao = request.form.get('composicao')
        fornecedor = request.form.get('fornecedor')
        custo = request.form.get('custo')
        novo_tecido = Tecido(cod=cod, caracteristica=caracteristica, descricao=descricao,
                             cor=cor, composicao=composicao, fornecedor=fornecedor, custo=custo)
        db.session.add(novo_tecido)
        db.session.commit()
        flash("Tecido cadastrado com sucesso!", "success")
        return redirect(url_for('tecidos'))
    tecidos_list = Tecido.query.all()
    return render_template('tecidos.html', tecidos=tecidos_list)

@app.route('/cadastrar_tecido', methods=['GET', 'POST'])
@login_required
def cadastrar_tecido():
    if request.method == 'POST':
        cod = request.form.get('cod')
        caracteristica = request.form.get('caracteristica')
        descricao = request.form.get('descricao')
        cor = request.form.get('cor')
        composicao = request.form.get('composicao')
        fornecedor = request.form.get('fornecedor')
        custo = request.form.get('custo')
        novo_tecido = Tecido(cod=cod, caracteristica=caracteristica, descricao=descricao,
                             cor=cor, composicao=composicao, fornecedor=fornecedor, custo=custo)
        db.session.add(novo_tecido)
        db.session.commit()
        flash("Tecido cadastrado com sucesso!", "success")
        return redirect(url_for('tecidos'))
    return render_template('cadastrar_tecido.html')

@app.route('/editar_tecido/<int:tecido_id>', methods=['GET', 'POST'])
@login_required
def editar_tecido(tecido_id):
    tecido = Tecido.query.get_or_404(tecido_id)
    if request.method == 'POST':
        tecido.cod = request.form['cod']
        tecido.caracteristica = request.form.get('caracteristica')
        tecido.descricao = request.form.get('descricao')
        tecido.cor = request.form.get('cor')
        tecido.composicao = request.form.get('composicao')
        tecido.fornecedor = request.form.get('fornecedor')
        tecido.custo = request.form.get('custo')
        db.session.commit()
        flash("Tecido atualizado com sucesso!", "success")
        return redirect(url_for('tecidos'))
    return render_template('editar_tecido.html', tecido=tecido)

@app.route('/excluir_tecido/<int:tecido_id>')
@login_required
def excluir_tecido(tecido_id):
    tecido = Tecido.query.get_or_404(tecido_id)
    db.session.delete(tecido)
    db.session.commit()
    flash("Tecido excluído com sucesso!", "success")
    return redirect(url_for('tecidos'))

# Rotas para Acabamentos
@app.route('/acabamentos', methods=['GET', 'POST'])
def acabamentos():
    if request.method == 'POST':
        cod = request.form.get('cod')
        caracteristica = request.form.get('caracteristica')
        descricao = request.form.get('descricao')
        cor = request.form.get('cor')
        fornecedor = request.form.get('fornecedor')
        custo = request.form.get('custo')
        novo_acabamento = Acabamento(cod=cod, caracteristica=caracteristica, descricao=descricao,
                                     cor=cor, fornecedor=fornecedor, custo=custo)
        db.session.add(novo_acabamento)
        db.session.commit()
        flash("Acabamento cadastrado com sucesso!", "success")
        return redirect(url_for('acabamentos'))
    acabamentos_list = Acabamento.query.all()
    return render_template('acabamentos.html', acabamentos=acabamentos_list)

@app.route('/cadastrar_acabamento', methods=['GET', 'POST'])
@login_required
def cadastrar_acabamento():
    if request.method == 'POST':
        cod = request.form.get('cod')
        caracteristica = request.form.get('caracteristica')
        descricao = request.form.get('descricao')
        cor = request.form.get('cor')
        fornecedor = request.form.get('fornecedor')
        custo = request.form.get('custo')
        novo_acabamento = Acabamento(cod=cod, caracteristica=caracteristica, descricao=descricao,
                                     cor=cor, fornecedor=fornecedor, custo=custo)
        db.session.add(novo_acabamento)
        db.session.commit()
        flash("Acabamento cadastrado com sucesso!", "success")
        return redirect(url_for('acabamentos'))
    return render_template('cadastrar_acabamento.html')

@app.route('/editar_acabamento/<int:acabamento_id>', methods=['GET', 'POST'])
@login_required
def editar_acabamento(acabamento_id):
    acabamento = Acabamento.query.get_or_404(acabamento_id)
    if request.method == 'POST':
        acabamento.cod = request.form['cod']
        acabamento.caracteristica = request.form.get('caracteristica')
        acabamento.descricao = request.form.get('descricao')
        acabamento.cor = request.form.get('cor')
        acabamento.fornecedor = request.form.get('fornecedor')
        acabamento.custo = request.form.get('custo')
        db.session.commit()
        flash("Acabamento atualizado com sucesso!", "success")
        return redirect(url_for('acabamentos'))
    return render_template('editar_acabamento.html', acabamento=acabamento)

@app.route('/excluir_acabamento/<int:acabamento_id>')
@login_required
def excluir_acabamento(acabamento_id):
    acabamento = Acabamento.query.get_or_404(acabamento_id)
    db.session.delete(acabamento)
    db.session.commit()
    flash("Acabamento excluído com sucesso!", "success")
    return redirect(url_for('acabamentos'))
    
    
# Rotas para Backup/Restore
@app.route('/backup')
@login_required
def backup():
    tipos = [{"id": t.id, "nome": t.nome} for t in Tipo.query.all()]
    statuses = [{"id": s.id, "nome": s.nome} for s in StatusProduto.query.all()]
    designers = [{"id": d.id, "nome": d.nome} for d in Designer.query.all()]
    equipes = [{"id": e.id, "nome": e.nome} for e in Equipe.query.all()]
    produtos = []
    for p in Produto.query.all():
        produtos.append({
            "id": p.id,
            "nome": p.nome,
            "descricao": p.descricao,
            "detalhe_tecnico": p.detalhamento_tecnico,
            "tipo_id": p.tipo_id,
            "status_id": p.status_id,
            "designer_id": p.designer_id,
            "equipe_id": p.equipe_id,
            "colecao_id": p.colecao_id,
            "foto_tumblr": p.foto_tumblr,
            "foto_360": p.foto_360,
            "usar_360": p.usar_360,
            "royalties": p.royalties,
            "restricao_tecido": p.restricao_tecido,
            "marca_artsofas": p.marca_artsofas,
            "materia_prima_terceirizada": p.materia_prima_terceirizada,
            "desenho_tecnico": p.desenho_tecnico
        })
    backup_data = {
        "tipos": tipos,
        "statuses": statuses,
        "designers": designers,
        "equipes": equipes,
        "produtos": produtos
    }
    backup_json = json.dumps(backup_data, indent=4, ensure_ascii=False)
    response = Response(backup_json, mimetype='application/json')
    response.headers["Content-Disposition"] = "attachment; filename=backup_portfolio.json"
    return response

@app.route('/restore', methods=['GET', 'POST'])
@login_required
def restore():
    if request.method == 'POST':
        file = request.files.get('backup_file')
        if not file:
            flash("Nenhum arquivo enviado", "danger")
            return redirect(url_for('restore'))
        try:
            data = json.load(file)
            Produto.query.delete()
            Tipo.query.delete()
            StatusProduto.query.delete()
            Designer.query.delete()
            Equipe.query.delete()
            Colecao.query.delete()
            db.session.commit()
            tipos_map = {}
            for t in data.get("tipos", []):
                novo_tipo = Tipo(nome=t["nome"])
                db.session.add(novo_tipo)
                db.session.flush()
                tipos_map[t["id"]] = novo_tipo.id
            statuses_map = {}
            for s in data.get("statuses", []):
                novo_status = StatusProduto(nome=s["nome"])
                db.session.add(novo_status)
                db.session.flush()
                statuses_map[s["id"]] = novo_status.id
            designers_map = {}
            for d in data.get("designers", []):
                novo_designer = Designer(nome=d["nome"])
                db.session.add(novo_designer)
                db.session.flush()
                designers_map[d["id"]] = novo_designer.id
            equipes_map = {}
            for e in data.get("equipes", []):
                novo_equipe = Equipe(nome=e["nome"])
                db.session.add(novo_equipe)
                db.session.flush()
                equipes_map[e["id"]] = novo_equipe.id
            colecoes_map = {}
            for c in data.get("colecoes", []):
                nova_colecao = Colecao(nome=c["nome"])
                db.session.add(nova_colecao)
                db.session.flush()
                colecoes_map[c["id"]] = nova_colecao.id
            db.session.commit()
            for p in data.get("produtos", []):
                novo_produto = Produto(
                    nome=p["nome"],
                    descricao=p["descricao"],
                    detalhamento_tecnico=p.get("detalhe_tecnico"),
                    tipo_id=tipos_map.get(p["tipo_id"]),
                    status_id=statuses_map.get(p["status_id"]),
                    designer_id=designers_map.get(p["designer_id"]),
                    equipe_id=equipes_map.get(p["equipe_id"]),
                    colecao_id=colecoes_map.get(p["colecao_id"]) if p.get("colecao_id") else None,
                    foto_tumblr=p["foto_tumblr"],
                    foto_360=p["foto_360"],
                    usar_360=p.get("usar_360", False),
                    royalties=p.get("royalties"),
                    restricao_tecido=p.get("restricao_tecido"),
                    marca_artsofas=p.get("marca_artsofas", False),
                    materia_prima_terceirizada=p.get("materia_prima_terceirizada", False),
                    desenho_tecnico=p.get("desenho_tecnico")
                )
                db.session.add(novo_produto)
            db.session.commit()
            flash("Backup restaurado com sucesso!", "success")
            return redirect(url_for('configuracoes_page'))
        except Exception as e:
            flash("Erro ao restaurar backup: " + str(e), "danger")
            return redirect(url_for('restore'))
    return render_template('restore.html')

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists('/var/www/portfolio/instance/portfolio.db'):
            db.create_all()
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=5000, debug=True)
