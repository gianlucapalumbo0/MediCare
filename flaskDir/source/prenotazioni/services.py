import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime,timedelta
from flaskDir import db, app
from flaskDir.MediCare.model.entity.DocumentoSanitario import DocumentoSanitario
from flaskDir.MediCare.model.entity.EnteSanitario import EnteSanitario
from flaskDir.MediCare.model.entity.Medici import Medico
from flaskDir.MediCare.model.entity.MetodoPagamento import MetodoPagamento
from flaskDir.MediCare.model.entity.Paziente import Paziente
from flaskDir.MediCare.model.entity.Prenotazione import Prenotazione




class MedicoService:
    """

    """
    #Invece di fare operazioni di input output ad ogni richiesta, memorizzo listamedici
    _listaMedici = None
    _listaCentri = None

    @staticmethod
    def getMedico(idMedico):
        return Medico.query.filter_by(email=idMedico).first()


    @staticmethod
    def retrieveMedico(email, password):
        medico = db.session.scalar(sqlalchemy.select(Medico).where(Medico.email == email))
        if medico is None or not medico.check_password(password):
            return None
        return medico

    @classmethod
    def getListaMedici(cls):
        if cls._listaMedici is None:
            cls._listaMedici = Medico.query.all()
        return cls._listaMedici

    @classmethod
    def getListaCentri(cls):
        if cls._listaCentri is None:
            cls._listaCentri = Medico.query.filter(Medico.specializzazione == "Vaccini").all()
        return cls._listaCentri


    def filtraMedici(cls, specializzazione = None, citta = None):
        cls._listaMedici = cls.getListaMedici()

        if specializzazione is None and citta is None:
            return cls._listaMedici

        newList = []
        if specializzazione is not None and citta is not None:
            newList = [medico for medico in cls._listaMedici if medico.città == citta and medico.specializzazione == specializzazione]

        elif citta is not None:
            newList = [medico for medico in cls._listaMedici if medico.città == citta]

        elif specializzazione is not None:
            newList = [medico for medico in cls._listaMedici if medico.specializzazione == specializzazione]

        return newList

    def filtraMediciv2(cls, specializzazione = None, citta = None):
        cls._listaMedici = cls.getListaMedici()

        if specializzazione is None and citta is None:
            return cls._listaMedici

        listaFiltrata = []
        condizioniDaVerificare = []

        if specializzazione is not None:
            condizioniDaVerificare.append(lambda medico: medico.specializzazione == specializzazione)
        if citta is not None:
            condizioniDaVerificare.append(lambda medico: medico.città == citta)

        listaFiltrata = [medico for medico in cls._listaMedici if all(condition(medico) for condition in condizioniDaVerificare)]

        return listaFiltrata

    @classmethod
    def addMedicotoLista(cls, medico):
        cls._listaMedici = cls.getListaMedici()
        cls._listaMedici.append(medico)


    @classmethod
    def rimuoviMedico(cls,email):
        try:
            medico = Medico.query.filter_by(email=email).first()
            if medico:
                db.session.delete(medico)
                db.session.commit()
                return True
            else:
                return False
        except SQLAlchemyError as e:
            print("Errore durante l'eliminazione del medico: {}".format(e))
            # Rollback in caso di errore
            db.session.rollback()
            return False

class PazienteService:

    @staticmethod
    def retrievePaziente(email, password):
        paziente = db.session.scalar(sqlalchemy.select(Paziente).where(Paziente.email == email))
        if paziente is None or not paziente.check_password(password):
            return None
        return paziente
    @classmethod
    def getListaVaccini(cls, user):
        return DocumentoSanitario.query.filter_by(titolare=user.CF, tipo="Vaccino").all()

    @classmethod
    def getListaPrenotazioni(cls, user):
        return db.session.scalars(sqlalchemy.select(Prenotazione).where(Prenotazione.pazienteCF == user.CF))


    @classmethod
    def eliminaPaziente(cls, cf):
        try:
            Prenotazione.query.filter_by(pazienteCF=cf).delete()
            DocumentoSanitario.query.filter_by(titolare=cf).delete()
            MetodoPagamento.query.filter_by(beneficiario=cf).delete()
            paziente = Paziente.query.filter_by(CF=cf).first()
            if paziente:
                db.session.delete(paziente)
                db.session.commit()
                return True
            else:
                return False

        except SQLAlchemyError as e:
            print("Errore durante l'eliminazione del paziente: {}".format(e))
            # Rollback in caso di errore
            db.session.rollback()
            return False

class PrenotazioneService:

    @classmethod
    def getListaMedici(cls,specializzazione = None, citta= None):
        return MedicoService().filtraMedici(specializzazione,citta)

    @classmethod
    def getListaVaccini(cls,user):
        return PazienteService.getListaVaccini(user)

    @classmethod
    def getListaPrenotazioni(cls, user):
        return PazienteService.getListaPrenotazioni(user)

    @classmethod
    def getListaPrenotazioniMedico(cls, medico):
        medico=Medico.query.filter(Medico.email==medico).first()
        if medico.ente_sanitario is None:
            return db.session.scalars(sqlalchemy.select(Prenotazione).where(Prenotazione.medico == medico.email))
        else:
            return db.session.scalars(sqlalchemy.select(Prenotazione).where(Prenotazione.medico == medico.email or Prenotazione.medico == medico.ente_sanitario))

    @classmethod
    def confirmIsFree(cls, idmedico, data, ora):
        mese=datetime.now().strftime("%m")+"-"
        anno=datetime.now().strftime("%Y")+"-"
        data=str(anno)+str(mese)+str(data)
        prenotazioni = Prenotazione.query.filter_by(medico=idmedico, oraVisita=ora, dataVisita=data).first()
        if prenotazioni: #Se ci sono prenotazioni per quella data allora non è free
            return False
        return True

    @staticmethod
    def savePrenotazione (idmedico, data, ora, tipo, CF, prezzo, carta=None):

        try:
            medico=MedicoService().getMedico(idmedico)
            mese = datetime.now().strftime("%m") + "-"
            anno = datetime.now().strftime("%Y") + "-"
            data = str(anno) + str(mese) + str(data)
            prenotazione = Prenotazione()
            prenotazione.medico = idmedico
            prenotazione.pazienteCF = CF
            prenotazione.tipoVisita = tipo
            prenotazione.dataVisita = data
            prenotazione.oraVisita = ora
            prenotazione.prezzo = prezzo
            prenotazione.prenMed = medico
            if carta.isdigit():
                prenotazione.pagata = True


            db.session.add(prenotazione)

            db.session.commit()

        except SQLAlchemyError as e:
            print("Errore mentre salvavo la prenotazione: {}".format(e))

            db.session.rollback()

            return False
    @staticmethod
    def saveVaccino(idmedico, data, ora, tipo, CF, prezzo=0):

        try:
            medico=MedicoService().getMedico(idmedico)
            prenotazione = Prenotazione()
            prenotazione.medico = idmedico
            prenotazione.pazienteCF = CF
            prenotazione.tipoVisita = tipo
            prenotazione.dataVisita = data
            prenotazione.oraVisita = ora
            prenotazione.prezzo = prezzo
            prenotazione.prenMed = medico

            db.session.add(prenotazione)

            db.session.commit()

        except SQLAlchemyError as e:
            print("Errore mentre salvavo la prenotazione: {}".format(e))

            db.session.rollback()

            return False


    @classmethod
    def modificaPrenotazione(cls, id, data, ora):
        try:
            prenotazioni = Prenotazione.query.filter_by(ID=id).first()
            if prenotazioni:
                prenotazioni.dataVisita = data
                prenotazioni.oraVisita = ora
                db.session.commit()

                return True
            else:
                return False

        except SQLAlchemyError as e:
            print("Errore mentre modificavo la prenotazione: {}".format(e))

            db.session.rollback()

            return False

    @classmethod
    def getGiorniCorrenti(cls):
        # Ottenere la data corrente
        oggi = datetime.now()

        # Ottenere l'anno e il mese corrente
        anno_corrente = oggi.year
        mese_corrente = oggi.month

        # Calcolare il primo giorno del mese corrente
        primo_giorno_mese = datetime(anno_corrente, mese_corrente, 1)

        # Calcolare il primo giorno del mese successivo per ottenere l'ultimo giorno del mese corrente
        primo_giorno_mese_successivo = datetime(anno_corrente, mese_corrente + 1,1) if mese_corrente < 12 else datetime(anno_corrente + 1, 1, 1)
        ultimo_giorno_mese_corrente = primo_giorno_mese_successivo - timedelta(days=1)

        # Calcolare il numero di giorni nel mese corrente
        numero_giorni_mese_corrente = (ultimo_giorno_mese_corrente - primo_giorno_mese).days + 1

        return numero_giorni_mese_corrente
    @classmethod
    def confirmVaccino(cls, idmedico, data, ora):
        prenotazioni = Prenotazione.query.filter_by(medico=idmedico, oraVisita=ora, dataVisita=data).first()
        if prenotazioni: #Se ci sono prenotazioni per quella data allora non è free
            return False
        return True


class FascicoloService:

    @classmethod
    def getDocumentiSanitari(cls, cf):
        return DocumentoSanitario.query.filter_by(titolare=cf)


    @classmethod
    def addDocumento(cls,num,tipo,data,descrizione,richiamo,paziente):
        with app.app_context():
            documento=DocumentoSanitario()
            documento.NumeroDocumento=num
            documento.tipo=tipo
            documento.dataEmissione=data
            documento.descrizione=descrizione
            documento.richiamo=richiamo
            documento.titolare=paziente
            db.session.add(documento)
            db.session.commit()














