from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO
from model import escursione


class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        relazioni = EscursioneDAO.get_escursioni_punti_interesse()
        if relazioni is None:
            print("Errore nel caricamento delle relazioni.")
            return
        for relazione in relazioni:
            id_escursione = relazione["id_escursione"]
            id_punto = relazione["id_punto_interesse"]
            escursione = self.escursioni_map.get(id_escursione)
            punto= self.punti_interesse_map.get(id_punto)
            if escursione is not None and punto is not None:
                escursione.punti_interesse.add(punto)
                punto.escursioni.add(escursione)

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        #seleziono solamente le escursioni del parco scelto
        escursioni_disponibili = []
        for escursione in self.escursioni_map.values():
            if escursione.id_parco == id_parco:
                escursioni_disponibili.append(escursione)
        #faccio partire la ricorsione
        self._ricorsione(escursioni_disponibili,0,[],0,0,0, set(), max_giorni, max_budget)

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, escursioni: list, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set, max_giorni: int | None = None, max_budget: float | None = None):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        #controllo se il pacchetto corrente è il migliore
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo= pacchetto_parziale.copy()
            self._costo = costo_corrente

        #provo tutte le escursioni successive
        for i in range(start_index, len(escursioni)):
            escursione = escursioni[i]
            nuova_durata = durata_corrente + escursione.durata_giorni
            nuovo_costo = costo_corrente + escursione.costo

            #controllo il vincolo dei giorni
            if max_giorni is not None and nuova_durata > max_giorni:
                continue

            #controllo il vincolo del budget
            if max_budget is not None and nuovo_costo > max_budget:
                continue

            #controllo che non ci siano punti duplicati
            if not punti_usati.isdisjoint(escursione.punti_interesse):
                continue

            #calcolo il nuovo punteggio
            nuovi_punti = escursione.punti_interesse
            nuovo_valore = valore_corrente + sum(punto.voto_visitatori for punto in nuovi_punti)

            #aggiungo l'escursione al pacchetto
            pacchetto_parziale.append(escursione)

            #aggiorno i punti di interesse utilizzati
            punti_usati.update(nuovi_punti)

            #uso la chiamata ricorsiva
            self._ricorsione(escursioni, i+1, pacchetto_parziale, nuova_durata, nuovo_costo, nuovo_valore, punti_usati, max_giorni, max_budget)

            pacchetto_parziale.pop()
            punti_usati.difference_update(nuovi_punti)
