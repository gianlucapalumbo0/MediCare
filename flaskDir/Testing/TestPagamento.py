import pytest
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_utils import database_exists, create_database
from urllib.parse import quote
from flaskDir import app, db
from flaskDir.MediCare.model.entity.MetodoPagamento import MetodoPagamento
from flaskDir.MediCare.model.entity.Paziente import Paziente
from flaskDir.source.Pagamento.PagamentoService import PagamentoService


#pip install mysqlclient

@pytest.fixture(autouse=True, scope='session')
def setUp(request):
    # Configura il database di test
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:{quote('Gio210302DVK')}@localhost:3306/testmedicare"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True
    db.init_app(app)
    # Crea le tabelle del database di test
    with app.test_client():
        with app.app_context():
            #db.drop_all()

            if not database_exists(app.config["SQLALCHEMY_DATABASE_URI"]):
                create_database(app.config["SQLALCHEMY_DATABASE_URI"])

            db.create_all()

        def teardown():
            # Tuo codice di tearDown qui
            with app.app_context():
                db.session.close_all()
                db.drop_all()

        # Aggiungi la funzione di tearDown alla richiesta
        request.addfinalizer(teardown)


def test_addCarta():
    # Cambia il URI del database a quello di test

    with app.app_context():
        mario=Paziente()
        mario.nome="Mario"
        mario.cognome="Rossi"
        mario.email="mariorossi@gmail.com"
        mario.password_hash="cancello"
        mario.chiaveSPID=10
        mario.ISEE_ordinario=10000
        mario.CF="PROVAS029DGH6712"
        mario.cellulare="3312258345"
        mario.luogoNascita="Salerno"
        mario.dataNascita="2000-12-31"
        mario.domicilio="Salerno"
        mario.sesso="Maschio"
        db.session.add(mario)
        db.session.commit()

    with app.app_context():
        cvv = 123
        pan = "8342645371625349"
        titolare = "Nome Cognome"
        mese = 12
        anno = 2024
        meseStr = str(mese)
        annoStr = str(anno)
        beneficiario = "PROVAS029DGH6712"
        scadenza = meseStr + "/" + annoStr

        PagamentoService.addCarta(cvv, pan, titolare, scadenza, beneficiario)

        # Verifica che la carta sia stata inserita nel database di testmedicare
        carta_inserita = MetodoPagamento.query.filter_by(PAN=pan, beneficiario=beneficiario).first()
        paziente=Paziente.query.filter_by(CF=beneficiario).first()
        assert carta_inserita is not None
        assert carta_inserita.nome_titolare == 'Nome Cognome'
        assert carta_inserita.dataScadenza == '12/2024'
        assert carta_inserita.beneficiario == 'PROVAS029DGH6712'



# Paziente presente nel database
def test_mostraCarte1():
    with app.app_context():
        paziente_test = Paziente(CF='PROVAS029DGH6712', chiaveSPID=123, nome='Mario', cognome='Rossi',
                                 email='mariorossi@gmail.com', password_hash='mario', cellulare='3457895647',
                                 domicilio='Salerno', dataNascita='2000-12-31', luogoNascita='Salerno', sesso='maschio',
                                 ISEE_ordinario=23456)

        cf = paziente_test.CF
        listaCarte = list(PagamentoService.getMetodi(cf))

        assert all(metodopagamento.beneficiario == cf for metodopagamento in listaCarte)
        oracolo = MetodoPagamento.query.filter_by(beneficiario=cf).all()
        attributiOracolo = {(metodopagamento.PAN) for metodopagamento in oracolo}
        attributiListaCarte = {(metodopagamento.PAN) for metodopagamento in listaCarte}
        assert attributiOracolo == attributiListaCarte



# Paziente non presente nel database
def test_mostraCarte2():
    with app.app_context():
        paziente = "NTSASS02JDGH6563"
        listaCarte = PagamentoService.getMetodi(paziente)
        assert all(metodopagamento.beneficiario == paziente for metodopagamento in listaCarte)

        oracolo = MetodoPagamento.query.filter_by(beneficiario=paziente).all()
        attributiOracolo = {(metodopagamento.CVV) for metodopagamento in oracolo}
        attributiListaCarte = {(metodopagamento.CVV) for metodopagamento in listaCarte}
        assert attributiOracolo == attributiListaCarte


def test_eliminaCarta():

    with app.app_context():
        # Inserisci un metodo di pagamento di esempio nel database
        pan_di_test = '1234567890123456'
        paziente_test = Paziente.query.filter_by(CF="PROVAS029DGH6712").first()
        metodo_di_test = MetodoPagamento(CVV=123, PAN=pan_di_test, nome_titolare='Nome Cognome', dataScadenza='01/2025', beneficiario='PROVAS029DGH6712')
        db.session.add(metodo_di_test)
        db.session.commit()

        # Verifica che il metodo di pagamento sia stato inserito correttamente nel database
        assert MetodoPagamento.query.filter_by(PAN=pan_di_test,beneficiario=paziente_test.CF).count() == 1

        # Chiamata al metodo eliminaMetodo
        PagamentoService.eliminaMetodo(pan_di_test,paziente_test.CF)

        # Verifica che il metodo di pagamento sia stato eliminato correttamente
        assert MetodoPagamento.query.filter_by(PAN=pan_di_test).count() == 0





