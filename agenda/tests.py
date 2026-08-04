from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clientes.models import Cliente
from locacoes.models import Locacao


class AgendaListTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Construtora Forte",
            documento="12.345.678/0001-90",
        )

    def test_lista_entrega_e_devolucao_da_locacao(self):
        hoje = timezone.localdate()
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=1),
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("agenda"))

        self.assertContains(response, "LOC-0001", count=2)
        self.assertContains(response, "Entrega")
        self.assertContains(response, "Devolucao")

    def test_exibe_calendario_semanal_com_eventos(self):
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio="2026-07-20",
            data_fim="2026-07-25",
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("agenda"), {"data": "2026-07-20"})

        self.assertContains(response, "20/07/2026 - 26/07/2026")
        self.assertContains(response, "Resumo da agenda")
        self.assertContains(response, "Eventos no periodo")
        self.assertContains(response, "Seg 20/07")
        self.assertContains(response, "Sab 25/07")
        self.assertContains(response, "Hora")
        self.assertContains(response, "calendar-event-entrega")
        self.assertContains(response, "calendar-event-devolucao")
        self.assertContains(response, "09:00 - LOC-0001")
        self.assertContains(response, "15:00 - LOC-0001")

    def test_calendario_preserva_filtros_na_navegacao(self):
        response = self.client.get(reverse("agenda"), {"data": "2026-07-20", "tipo": "entrega", "q": "Forte"})

        self.assertContains(response, "data=2026-07-13&amp;view=semana&amp;q=Forte&amp;tipo=entrega")
        self.assertContains(response, "data=2026-07-27&amp;view=semana&amp;q=Forte&amp;tipo=entrega")

    def test_alterna_entre_visualizacao_semana_e_lista(self):
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio="2026-07-20",
            data_fim="2026-07-25",
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("agenda"), {"data": "2026-07-20", "view": "semana"})
        self.assertContains(response, "calendar-week")
        self.assertContains(response, 'href="/agenda/?data=2026-07-20&amp;view=lista"')
        self.assertContains(response, 'aria-disabled="true"')

        response = self.client.get(reverse("agenda"), {"data": "2026-07-20", "view": "lista"})
        self.assertNotContains(response, "calendar-week")
        self.assertContains(response, 'href="/agenda/?data=2026-07-20&amp;view=semana"')
        self.assertContains(response, "<td>Entrega</td>", html=True)

    def test_filtra_eventos_por_tipo(self):
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio="2026-07-20",
            data_fim="2026-07-25",
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("agenda"), {"data": "2026-07-20", "tipo": "entrega"})

        self.assertContains(response, "calendar-event-entrega")
        self.assertNotContains(response, "calendar-event-devolucao")

    def test_nao_lista_locacao_cancelada(self):
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio="2026-07-20",
            data_fim="2026-07-25",
            status=Locacao.Status.CANCELADA,
        )

        response = self.client.get(reverse("agenda"), {"view": "lista"})

        self.assertNotContains(response, "LOC-0001")
        self.assertContains(response, "Nenhum evento na agenda")

    def test_classifica_eventos_por_situacao(self):
        hoje = timezone.localdate()
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio=hoje - timedelta(days=3),
            data_fim=hoje,
            status=Locacao.Status.ATIVA,
        )
        Locacao.objects.create(
            codigo="LOC-0002",
            cliente=self.cliente,
            data_inicio=hoje + timedelta(days=1),
            data_fim=hoje + timedelta(days=5),
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("agenda"))

        self.assertContains(response, "Atrasado")
        self.assertContains(response, "Hoje")
        self.assertContains(response, "Proximo")
        self.assertContains(response, "Futuro")

    def test_filtra_eventos_por_situacao(self):
        hoje = timezone.localdate()
        Locacao.objects.create(
            codigo="LOC-0001",
            cliente=self.cliente,
            data_inicio=hoje - timedelta(days=3),
            data_fim=hoje - timedelta(days=1),
            status=Locacao.Status.ATIVA,
        )
        Locacao.objects.create(
            codigo="LOC-0002",
            cliente=self.cliente,
            data_inicio=hoje + timedelta(days=5),
            data_fim=hoje + timedelta(days=7),
            status=Locacao.Status.AGENDADA,
        )

        response = self.client.get(reverse("agenda"), {"data": hoje - timedelta(days=3), "situacao": "atrasado"})

        self.assertContains(response, "LOC-0001")
        self.assertNotContains(response, "LOC-0002")
