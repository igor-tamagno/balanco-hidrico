import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from pathlib import Path

# Configuração da página
st.set_page_config(page_title="Análise de Balanço Hídrico", page_icon="💧", layout="wide")

# Função para formatar ano_mes no padrão mmm/aa
def format_ano_mes(ano_mes):
    """Converte ano_mes (formato YYYYMM) para mmm/aa (formato brasileiro)"""
    try:
        ano_mes_str = str(int(ano_mes))
        if len(ano_mes_str) != 6:
            return ano_mes_str
        
        ano = ano_mes_str[:4]
        mes = ano_mes_str[4:6]
        
        meses_pt = {
            '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
            '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
            '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
        }
        
        mes_abrev = meses_pt.get(mes, mes)
        ano_abrev = ano[-2:]  # Últimos 2 dígitos do ano
        
        return f"{mes_abrev}/{ano_abrev}"
    except:
        return str(ano_mes)

# Função para formatar números no padrão brasileiro
def format_number_br(value, decimals=0):
    """Formatar números no padrão brasileiro: . para milhares, , para decimais"""
    if pd.isna(value) or value == 0:
        return "0"
    
    if decimals == 0:
        return f"{value:,.0f}".replace(",", ".")
    else:
        formatted = f"{value:,.{decimals}f}"
        # Substituir separadores: primeiro vírgula por ponto temporário
        formatted = formatted.replace(",", "TEMP")
        # Substituir ponto por vírgula (decimais)
        formatted = formatted.replace(".", ",")
        # Substituir temporário por ponto (milhares)
        formatted = formatted.replace("TEMP", ".")
        return formatted

# Cores e dados
CORES_PERSONALIZADAS = {
    'Volume de Entrada': 'rgba(255, 255, 255, 0.7)', 'Consumo Autorizado': 'rgba(16, 72, 97, 0.7)',
    'Consumo Autorizado Faturado': 'rgba(131, 204, 235, 0.7)', 'Volume Medido': 'rgba(192, 230, 245, 0.7)',
    'Autorizado não Faturado': 'rgba(131, 204, 235, 0.7)', 'Uso Operacional': 'rgba(192, 230, 245, 0.7)',
    'Uso Emergencial': 'rgba(255, 217, 217, 0.7)', 'Uso Social': 'rgba(255, 217, 217, 0.7)',
    'Volume de Perdas': 'rgba(120, 0, 0, 0.7)', 'Perdas Aparentes': 'rgba(165, 42, 42, 0.7)',
    'Clandestinos': 'rgba(255, 217, 217, 0.7)', 'Fraudes': 'rgba(255, 217, 217, 0.7)',
    'Submedição': 'rgba(255, 217, 217, 0.7)', 'Perdas Reais': 'rgba(165, 42, 42, 0.7)',
    'Vazamento em Ramais': 'rgba(255, 217, 217, 0.7)', 'Outros Vazamentos': 'rgba(255, 217, 217, 0.7)',
}

cores_categoria = {'A': "#83CCEB", 'B': '#FFE07D', 'C': '#ED9283', 'D': '#D63031'}
cores_categoria_bg = {'A': 'rgba(131, 204, 235, 0.8)', 'B': 'rgba(255, 224, 125, 0.8)', 'C': 'rgba(237, 146, 131, 0.8)', 'D': 'rgba(214, 48, 49, 0.8)'}
cores_classificacao = {'A': 'rgba(131, 204, 235, 0.5)', 'B': 'rgba(255, 224, 125, 0.5)', 'C': 'rgba(237, 146, 131, 0.5)', 'D': 'rgba(214, 48, 49, 0.5)'}

def get_matriz_banco_mundial():
    return {
        'categorias': {
            'A': {'descricao': 'Redução adicional de perda pode não ser econômica, a menos que haja insuficiência de abastecimento; são necessárias análises mais criteriosas para identificar o custo efetivo da melhoria'},
            'B': {'descricao': 'Potencial para melhorias significativas; considerar o gerenciamento de pressão; práticas melhores de controle ativo de vazamentos, e uma melhor manutenção da rede'},
            'C': {'descricao': 'Registro deficiente de vazamentos; tolerável somente se a água é abundante e barata; mesmo assim, analise o nível e a natureza dos vazamentos e intensifique os esforços para redução de vazamentos'},
            'D': {'descricao': 'Uso muito ineficiente dos recursos; programa de redução de vazamentos é imperativo e altamente prioritário'}
        },
        'perdas_por_pressao': {
            '10m': {'A': '< 50', 'B': '50-100', 'C': '100-200', 'D': '> 200'},
            '20m': {'A': '< 100', 'B': '100-200', 'C': '200-400', 'D': '> 400'},
            '30m': {'A': '< 150', 'B': '150-300', 'C': '300-600', 'D': '> 600'},
            '40m': {'A': '< 200', 'B': '200-400', 'C': '400-800', 'D': '> 800'},
            '50m': {'A': '< 250', 'B': '250-500', 'C': '500-1000', 'D': '> 1.000'}
        },
        'recomendacoes': {
            'A': [
                {
                    'titulo': 'Investigação das opções de melhoria do gerenciamento de pressão',
                    'subtopicos': [
                        'Realizar inspeções regulares das válvulas redutoras existentes',
                        'Monitorar manualmente pressões em pontos críticos da rede',
                        'Ajustar operação de bombas conforme demanda horária'
                    ]
                },
                {
                    'titulo': 'Investigação das possibilidades de melhoria da rapidez e qualidade dos reparos',
                    'subtopicos': [
                        'Organizar kits de ferramentas e materiais por tipo de reparo',
                        'Estabelecer procedimentos padronizados para reparos emergenciais',
                        'Criar sistema de comunicação direta entre equipes de campo'
                    ]
                },
                {
                    'titulo': 'Revisão da frequência econômica de intervenções',
                    'subtopicos': [
                        'Analisar registros de manutenções para identificar padrões',
                        'Priorizar intervenções baseadas em histórico de falhas',
                        'Documentar custos operacionais de cada tipo de intervenção'
                    ]
                },
                {
                    'titulo': 'Introdução / melhoria do controle ativo de vazamentos',
                    'subtopicos': [
                        'Implementar rondas sistemáticas de detecção acústica',
                        'Treinar operadores para identificação visual de vazamentos',
                        'Estabelecer rotinas de inspeção noturna em áreas críticas'
                    ]
                },
                {
                    'titulo': 'Avaliação do nível econômico de vazamentos',
                    'subtopicos': [
                        'Quantificar perdas por setor através de medições de campo',
                        'Registrar tempo e recursos gastos em cada reparo',
                        'Mapear vazamentos recorrentes para ação prioritária'
                    ]
                }
            ],
            'B': [
                {
                    'titulo': 'Investigação das opções de melhoria do gerenciamento de pressão',
                    'subtopicos': [
                        'Realizar inspeções regulares das válvulas redutoras existentes',
                        'Monitorar manualmente pressões em pontos críticos da rede',
                        'Ajustar operação de bombas conforme demanda horária'
                    ]
                },
                {
                    'titulo': 'Investigação das possibilidades de melhoria da rapidez e qualidade dos reparos',
                    'subtopicos': [
                        'Organizar kits de ferramentas e materiais por tipo de reparo',
                        'Estabelecer procedimentos padronizados para reparos emergenciais',
                        'Criar sistema de comunicação direta entre equipes de campo'
                    ]
                },
                {
                    'titulo': 'Revisão da frequência econômica de intervenções',
                    'subtopicos': [
                        'Analisar registros de manutenções para identificar padrões',
                        'Priorizar intervenções baseadas em histórico de falhas',
                        'Documentar custos operacionais de cada tipo de intervenção'
                    ]
                },
                {
                    'titulo': 'Introdução / melhoria do controle ativo de vazamentos',
                    'subtopicos': [
                        'Implementar rondas sistemáticas de detecção acústica',
                        'Treinar operadores para identificação visual de vazamentos',
                        'Estabelecer rotinas de inspeção noturna em áreas críticas'
                    ]
                },
                {
                    'titulo': 'Identificação de opções para melhorar os procedimentos de manutenção',
                    'subtopicos': [
                        'Padronizar sequência de atividades para manutenção preventiva',
                        'Criar check-lists operacionais para cada tipo de serviço',
                        'Estabelecer rotinas de limpeza e conservação de equipamentos'
                    ]
                },
                {
                    'titulo': 'Avaliação do nível econômico de vazamentos',
                    'subtopicos': [
                        'Quantificar perdas por setor através de medições de campo',
                        'Registrar tempo e recursos gastos em cada reparo',
                        'Mapear vazamentos recorrentes para ação prioritária'
                    ]
                },
                {
                    'titulo': 'Revisão das frequências de arrebentamentos',
                    'subtopicos': [
                        'Documentar todas as ocorrências com localização e causa',
                        'Identificar trechos com maior incidência de rompimentos',
                        'Programar inspeções preventivas em tubulações críticas'
                    ]
                },
                {
                    'titulo': 'Revisão das políticas de gerenciamento de ativos',
                    'subtopicos': [
                        'Atualizar cadastro de equipamentos e tubulações em campo',
                        'Registrar condições operacionais dos ativos durante manutenções',
                        'Propor cronograma de substituições baseado em observações técnicas'
                    ]
                }
            ],
            'C': [
                {
                    'titulo': 'Investigação das opções de melhoria do gerenciamento de pressão',
                    'subtopicos': [
                        'Realizar inspeções regulares das válvulas redutoras existentes',
                        'Monitorar manualmente pressões em pontos críticos da rede',
                        'Ajustar operação de bombas conforme demanda horária'
                    ]
                },
                {
                    'titulo': 'Investigação das possibilidades de melhoria da rapidez e qualidade dos reparos',
                    'subtopicos': [
                        'Organizar kits de ferramentas e materiais por tipo de reparo',
                        'Estabelecer procedimentos padronizados para reparos emergenciais',
                        'Criar sistema de comunicação direta entre equipes de campo'
                    ]
                },
                {
                    'titulo': 'Introdução / melhoria do controle ativo de vazamentos',
                    'subtopicos': [
                        'Implementar rondas sistemáticas de detecção acústica',
                        'Treinar operadores para identificação visual de vazamentos',
                        'Estabelecer rotinas de inspeção noturna em áreas críticas'
                    ]
                },
                {
                    'titulo': 'Identificação de opções para melhorar os procedimentos de manutenção',
                    'subtopicos': [
                        'Padronizar sequência de atividades para manutenção preventiva',
                        'Criar check-lists operacionais para cada tipo de serviço',
                        'Estabelecer rotinas de limpeza e conservação de equipamentos'
                    ]
                },
                {
                    'titulo': 'Revisão das frequências de arrebentamentos',
                    'subtopicos': [
                        'Documentar todas as ocorrências com localização e causa',
                        'Identificar trechos com maior incidência de rompimentos',
                        'Programar inspeções preventivas em tubulações críticas'
                    ]
                },
                {
                    'titulo': 'Revisão das políticas de gerenciamento de ativos',
                    'subtopicos': [
                        'Atualizar cadastro de equipamentos e tubulações em campo',
                        'Registrar condições operacionais dos ativos durante manutenções',
                        'Propor cronograma de substituições baseado em observações técnicas'
                    ]
                },
                {
                    'titulo': 'Redução das deficiências de mão de obra, treinamento e comunicações',
                    'subtopicos': [
                        'Organizar treinamentos internos entre equipes experientes',
                        'Estabelecer reuniões operacionais para troca de informações',
                        'Criar sistema de comunicação via rádio entre equipes'
                    ]
                },
                {
                    'titulo': 'Planejamento quinquenal para alcançar melhor enquadramento nas categorias de desempenho',
                    'subtopicos': [
                        'Estabelecer metas operacionais mensuráveis por equipe',
                        'Implementar controle diário de indicadores de performance',
                        'Criar cronograma de ações operacionais prioritárias'
                    ]
                }
            ],
            'D': [
                {
                    'titulo': 'Revisão das políticas de gerenciamento de ativos',
                    'subtopicos': [
                        'Atualizar cadastro de equipamentos e tubulações em campo',
                        'Registrar condições operacionais dos ativos durante manutenções',
                        'Propor cronograma de substituições baseado em observações técnicas'
                    ]
                },
                {
                    'titulo': 'Redução das deficiências de mão de obra, treinamento e comunicações',
                    'subtopicos': [
                        'Organizar treinamentos internos entre equipes experientes',
                        'Estabelecer reuniões operacionais para troca de informações',
                        'Criar sistema de comunicação via rádio entre equipes'
                    ]
                },
                {
                    'titulo': 'Planejamento quinquenal para alcançar melhor enquadramento nas categorias de desempenho',
                    'subtopicos': [
                        'Estabelecer metas operacionais mensuráveis por equipe',
                        'Implementar controle diário de indicadores de performance',
                        'Criar cronograma de ações operacionais prioritárias'
                    ]
                },
                {
                    'titulo': 'Revisão geral de todas as atividades e procedimentos',
                    'subtopicos': [
                        'Documentar rotinas operacionais atuais de cada equipe',
                        'Identificar gargalos operacionais através de observação direta',
                        'Propor melhorias baseadas na experiência prática das equipes'
                    ]
                }
            ]
        }
    }

def buscar_dados_sigis(df_sigis, codigo_sigis, data_range, localidades_filtradas):
    """Busca dados específicos do SIGIS para um código"""
    if df_sigis is None:
        return 0
    
    try:
        # Filtrar pelo código SIGIS (coluna A)
        mask_codigo = df_sigis.iloc[:, 0] == codigo_sigis
        resultados = df_sigis[mask_codigo].copy()
        
        if resultados.empty:
            return 0
        
        # Filtrar por período
        if 'ano_mes' in resultados.columns:
            resultados = resultados[
                (resultados['ano_mes'] >= data_range[0]) & 
                (resultados['ano_mes'] <= data_range[1])
            ]
        
        if resultados.empty:
            return 0
        
        # Filtrar pelas localidades válidas
        if localidades_filtradas:
            if 'cod_localidade' in resultados.columns:
                resultados = resultados[resultados['cod_localidade'].isin(localidades_filtradas)]
            elif 'nome_localidade' in resultados.columns:
                resultados = resultados[resultados['nome_localidade'].isin(localidades_filtradas)]
        
        if resultados.empty:
            return 0
        
        # Somar todos os valores da coluna I (índice 8)
        total = 0
        for _, row in resultados.iterrows():
            valor = row.iloc[8]  # Coluna I
            if pd.notna(valor):
                try:
                    valor_float = float(valor)
                    if valor_float > 0:
                        total += valor_float
                except (ValueError, TypeError):
                    continue
        
        return total
        
    except Exception as e:
        print(f"Erro ao buscar dados SIGIS para código {codigo_sigis}: {e}")
        return 0

def calcular_ivi(perdas_reais_valor, volume_entrada, df_sigis=None, data_range=None, localidades_filtradas=None):
    """
    Calcula o IVI (Índice de Vazamento da Infraestrutura) e categoria segundo Banco Mundial
    Classificação baseada na matriz de localização IVI x IPL
    """
    
    # Converter para float
    try:
        perdas_reais_valor = float(perdas_reais_valor) if perdas_reais_valor != '' else 0
        volume_entrada = float(volume_entrada) if volume_entrada != '' else 0
    except (ValueError, TypeError):
        return 'N/A', 'N/A', 0, 0
    
    if volume_entrada == 0: 
        return 'N/A', 'N/A', 0, 0
    
    # Buscar dados do SIGIS usando último valor não zerado
    num_ligacoes = 0
    extensao_rede_km = 0
    
    if df_sigis is not None and data_range is not None:
        num_ligacoes = buscar_ultimo_valor_nao_zerado_simples(df_sigis, 9603, data_range, localidades_filtradas)
        extensao_rede_km = buscar_ultimo_valor_nao_zerado_simples(df_sigis, 33, data_range, localidades_filtradas)
    
    if num_ligacoes == 0 or extensao_rede_km == 0:
        return 'N/A', 'N/A', 0, 0
    
    # Calcular dias do período
    if data_range is None:
        dias_periodo = 30
    else:
        from datetime import datetime
        import calendar
        
        data_inicio, data_fim = data_range
        
        if data_inicio == data_fim:
            ano = data_inicio // 100
            mes = data_inicio % 100
            dias_periodo = calendar.monthrange(ano, mes)[1]
        else:
            ano_inicio = data_inicio // 100
            mes_inicio = data_inicio % 100
            ano_fim = data_fim // 100
            mes_fim = data_fim % 100
            
            dt_inicio = datetime(ano_inicio, mes_inicio, 1)
            ultimo_dia_mes_fim = calendar.monthrange(ano_fim, mes_fim)[1]
            dt_fim = datetime(ano_fim, mes_fim, ultimo_dia_mes_fim)
            
            diferenca = dt_fim - dt_inicio
            dias_periodo = diferenca.days + 1
    
    # PRAC = Perdas Reais do período ÷ dias (converter para base diária)
    prac = perdas_reais_valor / dias_periodo
    
    # PRAI = Perdas Reais Anuais Inevitáveis (m³/dia)
    pressao_media = 30
    tma = 24
    
    perdas_ligacoes = 0.8 * num_ligacoes
    perdas_rede = 18 * extensao_rede_km
    
    prai_litros_dia = (perdas_ligacoes + perdas_rede) * pressao_media * tma / 24
    prai = prai_litros_dia / 1000
    
    # IVI = PRAC (m³/dia) ÷ PRAI (m³/dia)
    ivi = prac / prai if prai > 0 else 0
    
    # CALCULAR IPL PARA CLASSIFICAÇÃO COMBINADA
    ipl = calcular_ipl(df_sigis, data_range, localidades_filtradas) if df_sigis is not None else 0
    
    # CLASSIFICAÇÃO BASEADA NA MATRIZ DE LOCALIZAÇÃO
    def classificar_por_matriz(ivi_valor, ipl_valor, pressao=30):
        """
        Classifica baseado na matriz de localização:
        1. IVI determina a linha (categoria base)
        2. Pressão determina a coluna (30m)
        3. IPL deve estar dentro da faixa da célula correspondente
        """
        
        # PASSO 1: Determinar categoria base pelo IVI
        if ivi_valor <= 4:
            categoria_ivi = 'A'
        elif ivi_valor <= 8:
            categoria_ivi = 'B'
        elif ivi_valor <= 16:
            categoria_ivi = 'C'
        else:
            categoria_ivi = 'D'
        
        # PASSO 2: Definir faixas IPL para pressão 30m
        faixas_ipl_30m = {
            'A': (0, 150),      # < 150
            'B': (150, 300),    # 150-300
            'C': (300, 600),    # 300-600
            'D': (600, float('inf'))  # > 600
        }
        
        # PASSO 3: Verificar se IPL está na faixa esperada para a categoria IVI
        faixa_esperada = faixas_ipl_30m[categoria_ivi]
        
        if faixa_esperada[0] <= ipl_valor < faixa_esperada[1]:
            # IPL está na faixa correta para a categoria IVI
            return categoria_ivi
        else:
            # IPL não está na faixa esperada, determinar categoria real pelo IPL
            for cat, (min_ipl, max_ipl) in faixas_ipl_30m.items():
                if min_ipl <= ipl_valor < max_ipl:
                    return cat
            
            # Se IPL for muito alto, retornar D
            return 'D'
    
    # Aplicar classificação por matriz
    categoria_final = classificar_por_matriz(ivi, ipl, pressao_media)
    
    return categoria_final, ivi, prac, prai

def calcular_ipl(df_sigis=None, data_range=None, localidades_filtradas=None):
    """
    Calcula IPL (Índice de Perdas por Ligação) baseado na fórmula oficial do SIGIS
    
    Automaticamente detecta se é:
    - Uma localidade: IPL direto
    - Múltiplas localidades: IPL agregado (soma volumes + soma ligações últimos valores)
    
    Fórmula: IPL = 1000 × (Prod + Imp - Exp - ∑Oper - Cons) / (Lig × Dias)
    """
    if df_sigis is None or data_range is None:
        return 0
    
    try:
        from datetime import datetime
        import calendar
        
        # Códigos SIGIS conforme documentação oficial
        codigo_producao = 1      # Volume Produzido de Água
        codigo_importado = 67    # Volume Importado
        codigo_exportado = 68    # Volume Exportado
        codigo_uso_op_1 = 29     # Descarga de rede
        codigo_uso_op_2 = 30     # Quebra de rede por terceiros
        codigo_uso_op_3 = 31     # Limpeza sanitária de reservatórios
        codigo_uso_op_4 = 32     # Utilização do corpo de bombeiros
        codigo_consumido = 9642  # Volume Consumido de água
        codigo_ligacoes = 9603   # Ligações reais de água faturadas
        
        # Buscar volumes do período (soma) - funciona igual para 1 ou N localidades
        volume_producao = buscar_dados_sigis(df_sigis, codigo_producao, data_range, localidades_filtradas)
        volume_importado = buscar_dados_sigis(df_sigis, codigo_importado, data_range, localidades_filtradas)
        volume_exportado = buscar_dados_sigis(df_sigis, codigo_exportado, data_range, localidades_filtradas)
        volume_uso_op_1 = buscar_dados_sigis(df_sigis, codigo_uso_op_1, data_range, localidades_filtradas)
        volume_uso_op_2 = buscar_dados_sigis(df_sigis, codigo_uso_op_2, data_range, localidades_filtradas)
        volume_uso_op_3 = buscar_dados_sigis(df_sigis, codigo_uso_op_3, data_range, localidades_filtradas)
        volume_uso_op_4 = buscar_dados_sigis(df_sigis, codigo_uso_op_4, data_range, localidades_filtradas)
        volume_consumido = buscar_dados_sigis(df_sigis, codigo_consumido, data_range, localidades_filtradas)
        
        # Buscar ligações - a função já detecta se é 1 ou N localidades automaticamente
        ligacoes_reais = buscar_ultimo_valor_nao_zerado_simples(df_sigis, codigo_ligacoes, data_range, localidades_filtradas)
        
        # Verificar se há dados suficientes
        if ligacoes_reais == 0:
            return 0
        
        # Calcular número real de dias do período
        if not isinstance(data_range, tuple) or len(data_range) != 2:
            dias_periodo = 30  # Default
        else:
            data_inicio, data_fim = data_range
            
            if data_inicio == data_fim:
                # Mesmo mês - calcular dias do mês
                ano = data_inicio // 100
                mes = data_inicio % 100
                dias_periodo = calendar.monthrange(ano, mes)[1]
            else:
                # Períodos diferentes - calcular dias totais
                ano_inicio = data_inicio // 100
                mes_inicio = data_inicio % 100
                ano_fim = data_fim // 100
                mes_fim = data_fim % 100
                
                # Data de início (primeiro dia do mês inicial)
                dt_inicio = datetime(ano_inicio, mes_inicio, 1)
                
                # Data de fim (último dia do mês final)
                ultimo_dia_mes_fim = calendar.monthrange(ano_fim, mes_fim)[1]
                dt_fim = datetime(ano_fim, mes_fim, ultimo_dia_mes_fim)
                
                # Calcular diferença em dias
                diferenca = dt_fim - dt_inicio
                dias_periodo = diferenca.days + 1  # +1 para incluir o último dia
        
        # Somar volumes operacionais
        volume_operacional_total = volume_uso_op_1 + volume_uso_op_2 + volume_uso_op_3 + volume_uso_op_4
        
        # Aplicar fórmula IPL
        numerador = volume_producao + volume_importado - volume_exportado - volume_operacional_total - volume_consumido
        denominador = ligacoes_reais * dias_periodo
        
        if denominador == 0:
            return 0
        
        ipl_calculado = (1000 * numerador) / denominador
        
        return max(0, ipl_calculado)
        
    except Exception as e:
        print(f"Erro ao calcular IPL: {e}")
        return 0

def buscar_ultimo_valor_nao_zerado_simples(df_sigis, codigo_sigis, data_range, localidades_filtradas):
    """Busca o último valor não zerado para dados de estoque (como ligações)"""
    if df_sigis is None:
        return 0
    
    try:
        # Filtrar pelo código SIGIS
        mask_codigo = df_sigis.iloc[:, 0] == codigo_sigis
        resultados = df_sigis[mask_codigo].copy()
        
        if resultados.empty:
            mask_codigo_str = df_sigis.iloc[:, 0].astype(str) == str(codigo_sigis)
            resultados = df_sigis[mask_codigo_str].copy()
        
        if resultados.empty:
            return 0
        
        # Filtrar por período
        if 'ano_mes' in resultados.columns:
            resultados = resultados[
                (resultados['ano_mes'] >= data_range[0]) & 
                (resultados['ano_mes'] <= data_range[1])
            ]
        
        if resultados.empty:
            return 0
        
        # Verificar se existe a coluna I (índice 8)
        if len(resultados.columns) <= 8:
            return 0
        
        # Filtrar pelas localidades válidas
        if localidades_filtradas:
            if 'cod_localidade' in resultados.columns:
                resultados = resultados[resultados['cod_localidade'].isin(localidades_filtradas)]
            elif 'nome_localidade' in resultados.columns:
                resultados = resultados[resultados['nome_localidade'].isin(localidades_filtradas)]
        
        if resultados.empty:
            return 0
        
        # NOVA LÓGICA: Se há múltiplas localidades, somar último valor de cada uma
        if localidades_filtradas and len(localidades_filtradas) > 1:
            total_ligacoes = 0
            chave_agrupamento = 'cod_localidade' if 'cod_localidade' in resultados.columns else 'nome_localidade'
            
            # Para cada localidade, buscar último valor não zerado
            for localidade_id in resultados[chave_agrupamento].unique():
                dados_localidade = resultados[resultados[chave_agrupamento] == localidade_id]
                dados_localidade = dados_localidade.sort_values('ano_mes', ascending=False)
                
                # Buscar último valor não zerado desta localidade
                for _, row in dados_localidade.iterrows():
                    valor = row.iloc[8]  # Coluna I
                    if pd.notna(valor):
                        try:
                            valor_float = float(valor)
                            if valor_float > 0:
                                total_ligacoes += valor_float
                                break  # Só o último valor não zerado desta localidade
                        except (ValueError, TypeError):
                            continue
            
            return total_ligacoes
        
        else:
            # LÓGICA ORIGINAL: Uma localidade ou nenhum filtro específico
            # Ordenar por ano_mes decrescente para pegar o mais recente
            if 'ano_mes' in resultados.columns:
                resultados = resultados.sort_values('ano_mes', ascending=False)
            
            # Buscar primeiro valor não zerado (mais recente)
            for _, row in resultados.iterrows():
                valor = row.iloc[8]  # Coluna I
                if pd.notna(valor):
                    try:
                        valor_float = float(valor)
                        if valor_float > 0:
                            return valor_float
                    except (ValueError, TypeError):
                        continue
            
            return 0
        
    except Exception as e:
        print(f"Erro ao buscar último valor não zerado para código {codigo_sigis}: {e}")
        return 0

# FUNÇÃO PARA CRIAR DADOS DE EXEMPLO
def create_sample_data():
    """Cria dados de exemplo para demonstração"""
    import numpy as np
    
    # Dados de exemplo para o balanço hídrico
    sample_data = []
    
    # Estrutura hierárquica de exemplo
    hierarchy = {
        '1': {'parent': '', 'nome': 'Volume de Entrada', 'valor': 1000000},
        '2': {'parent': '1', 'nome': 'Consumo Autorizado', 'valor': 750000},
        '2.1': {'parent': '2', 'nome': 'Consumo Autorizado Faturado', 'valor': 650000},
        '2.1.1': {'parent': '2.1', 'nome': 'Volume Medido', 'valor': 600000},
        '2.2': {'parent': '2', 'nome': 'Autorizado não Faturado', 'valor': 100000},
        '2.2.1': {'parent': '2.2', 'nome': 'Uso Operacional', 'valor': 60000},
        '2.2.2': {'parent': '2.2', 'nome': 'Uso Emergencial', 'valor': 20000},
        '2.2.3': {'parent': '2.2', 'nome': 'Uso Social', 'valor': 20000},
        '3': {'parent': '1', 'nome': 'Volume de Perdas', 'valor': 250000},
        '3.1': {'parent': '3', 'nome': 'Perdas Aparentes', 'valor': 100000},
        '3.1.1': {'parent': '3.1', 'nome': 'Clandestinos', 'valor': 30000},
        '3.1.2': {'parent': '3.1', 'nome': 'Fraudes', 'valor': 20000},
        '3.1.3': {'parent': '3.1', 'nome': 'Submedição', 'valor': 50000},
        '3.2': {'parent': '3', 'nome': 'Perdas Reais', 'valor': 150000},
        '3.2.1': {'parent': '3.2', 'nome': 'Vazamento em Ramais', 'valor': 80000},
        '3.2.2': {'parent': '3.2', 'nome': 'Outros Vazamentos', 'valor': 70000}
    }
    
    # Criar dados para 3 localidades e 6 meses
    localidades = [
        {'cod': 1001, 'nome': 'Centro', 'municipio': 'Cidade A', 'regional': 'Regional Norte'},
        {'cod': 1002, 'nome': 'Bairro Sul', 'municipio': 'Cidade A', 'regional': 'Regional Norte'},
        {'cod': 2001, 'nome': 'Industrial', 'municipio': 'Cidade B', 'regional': 'Regional Sul'}
    ]
    
    meses = [202401, 202402, 202403, 202404, 202405, 202406]
    
    for localidade in localidades:
        for mes in meses:
            for item_id, item_data in hierarchy.items():
                # Adicionar variação aleatória nos valores
                variacao = np.random.uniform(0.8, 1.2)
                valor = int(item_data['valor'] * variacao / 3)  # Dividir por 3 localidades
                
                nivel_info = f"Nível {len(item_id.split('.'))}"
                
                sample_data.append({
                    'cod_regional': localidade['regional'][:3].upper(),
                    'nome_regional': localidade['regional'],
                    'cod_municipio': localidade['cod'] // 1000,
                    'nome_municipio': localidade['municipio'],
                    'cod_localidade': localidade['cod'],
                    'nome_localidade': localidade['nome'],
                    'ano_mes': mes,
                    'id': item_id,
                    'parent': item_data['parent'],
                    'nivel_info': nivel_info,
                    'nome_info': item_data['nome'],
                    'valor': valor,
                    'valor_acum': valor
                })
    
    return pd.DataFrame(sample_data)

def create_sample_sigis_data():
    """Cria dados de exemplo do SIGIS"""
    import numpy as np
    
    # Códigos SIGIS importantes
    codigos = [1, 67, 68, 29, 30, 31, 32, 9642, 9603, 33]
    localidades = [1001, 1002, 2001]
    meses = [202401, 202402, 202403, 202404, 202405, 202406]
    
    sigis_data = []
    
    for codigo in codigos:
        for localidade in localidades:
            for mes in meses:
                if codigo == 9603:  # Ligações
                    valor = np.random.randint(800, 1200)
                elif codigo == 33:  # Extensão de rede
                    valor = np.random.uniform(15, 25)
                elif codigo in [1, 9642]:  # Volumes principais
                    valor = np.random.uniform(80000, 120000)
                else:  # Outros volumes
                    valor = np.random.uniform(1000, 5000)
                
                sigis_data.append([
                    codigo, 'Descrição', localidade, f'Localidade {localidade}',
                    mes, 'Unidade', 'Tipo', 'Fonte', valor
                ])
    
    columns = ['A', 'B', 'C', 'D', 'ano_mes', 'F', 'G', 'H', 'I']
    return pd.DataFrame(sigis_data, columns=columns)

# FUNÇÃO PRINCIPAL DE CARREGAMENTO DE DADOS
@st.cache_data
def load_data(uploaded_file):
    """Carrega dados do arquivo enviado"""
    
    if uploaded_file is not None:
        try:
            # Carregar planilha 1 (Balanço Hídrico)
            df = pd.read_excel(uploaded_file, sheet_name=0)  # Primeira planilha
            
            if df.empty:
                st.error("❌ A planilha de Balanço Hídrico (Planilha 1) está vazia!")
                return None, None
            
            expected_columns = ['cod_regional', 'nome_regional', 'cod_municipio', 'nome_municipio', 'cod_localidade', 'nome_localidade', 'ano_mes', 'id', 'parent', 'nivel_info', 'nome_info', 'valor', 'valor_acum']
            
            if len(df.columns) >= len(expected_columns):
                df.columns = expected_columns[:len(df.columns)]
            else:
                st.error(f"❌ A planilha de Balanço Hídrico deve ter pelo menos {len(expected_columns)} colunas.")
                return None, None
            
            df['parent'] = df['parent'].fillna("").astype(str).replace('nan', '')
            
            # Aplicar formatação de data na coluna ano_mes
            df['ano_mes_formatted'] = df['ano_mes'].apply(format_ano_mes)
            
            required_cols = ['nome_info', 'valor', 'id', 'parent', 'nivel_info']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                st.error(f"❌ Colunas obrigatórias faltando na planilha de Balanço Hídrico: {missing_cols}")
                return None, None
            
            # Carregar planilha 2 (SIGIS)
            df_sigis = None
            try:
                df_sigis = pd.read_excel(uploaded_file, sheet_name=1)  # Segunda planilha
                if not df_sigis.empty and 'ano_mes' in df_sigis.columns:
                    df_sigis['ano_mes_formatted'] = df_sigis['ano_mes'].apply(format_ano_mes)
                else:
                    st.warning("⚠️ A planilha SIGIS (Planilha 2) está vazia ou não possui a coluna 'ano_mes'.")
                    df_sigis = None
            except Exception as e:
                st.warning(f"⚠️ Erro ao carregar planilha SIGIS (Planilha 2): {e}")
                df_sigis = None
            
            return df, df_sigis
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {e}")
            return None, None
    
    else:
        # Sem arquivo carregado
        return None, None

# Restante das funções permanecem iguais...
def apply_hierarchical_filters(df, regional_sel, municipio_sel, localidade_sel):
    df_filtered = df.copy()
    if localidade_sel != "Todas":
        df_filtered = df_filtered[df_filtered['nome_localidade'] == localidade_sel]
        nivel = "localidade"
    elif municipio_sel != "Todos":
        df_filtered = df_filtered[df_filtered['nome_municipio'] == municipio_sel]
        nivel = "municipio"
    elif regional_sel != "Todas":
        df_filtered = df_filtered[df_filtered['nome_regional'] == regional_sel]
        nivel = "regional"
    else:
        nivel = "geral"
    return df_filtered, nivel

def create_hidrometros_table(df_filtered, df_sigis, data_range, regional_sel, municipio_sel, localidade_sel):
    """Cria tabela de hidrômetros apenas com dados reais do SIGIS"""
    
    if df_filtered.empty or df_sigis is None:
        return pd.DataFrame()
    
    # Buscar dados de submedição e volume medido dos dados filtrados
    volume_medido_data = df_filtered[df_filtered['nome_info'] == 'Volume Medido']['valor'].sum()
    
    if volume_medido_data == 0:
        return pd.DataFrame()
    
    # IDM por ano
    idm_values = [95.00, 93.50, 92.00, 90.30, 88.50, 86.80, 85.00, 83.00, 80.00, 77.00, 74.00, 71.00, 71.00, 71.00, 71.00, 71.00]
    
    # Códigos SIGIS
    codigos_hidrometros = list(range(7380, 7441, 4))
    codigos_volume = list(range(7444, 7505, 4))
    
    def buscar_valor_agregado(codigo_sigis):
        """Busca dados reais do SIGIS"""
        if df_sigis is None:
            return 0
        
        try:
            # Obter lista de localidades que passaram pelos filtros
            localidades_validas = set()
            
            if not df_filtered.empty:
                if 'cod_localidade' in df_filtered.columns:
                    localidades_validas = set(df_filtered['cod_localidade'].unique())
                elif 'nome_localidade' in df_filtered.columns:
                    localidades_validas = set(df_filtered['nome_localidade'].unique())
            
            # Filtrar df_sigis pelo código específico primeiro
            mask_codigo = df_sigis.iloc[:, 0] == codigo_sigis
            resultados = df_sigis[mask_codigo].copy()
            
            if resultados.empty:
                return 0
            
            # Filtrar por período
            if 'ano_mes' in resultados.columns:
                resultados = resultados[
                    (resultados['ano_mes'] >= data_range[0]) & 
                    (resultados['ano_mes'] <= data_range[1])
                ]
            
            if resultados.empty:
                return 0
            
            # Filtrar pelas localidades que passaram pelos filtros principais
            if localidades_validas:
                if 'cod_localidade' in resultados.columns:
                    resultados = resultados[resultados['cod_localidade'].isin(localidades_validas)]
                elif 'nome_localidade' in resultados.columns:
                    resultados = resultados[resultados['nome_localidade'].isin(localidades_validas)]
            
            if resultados.empty:
                return 0
            
            # Para cada localidade única, buscar último valor não zerado
            total = 0
            
            # Identificar chave de agrupamento
            chave_agrupamento = None
            if 'cod_localidade' in resultados.columns:
                chave_agrupamento = 'cod_localidade'
            elif 'nome_localidade' in resultados.columns:
                chave_agrupamento = 'nome_localidade'
            
            if chave_agrupamento and len(localidades_validas) > 0:
                # Agrupar por localidade e somar últimos valores não zerados
                for localidade_id in resultados[chave_agrupamento].unique():
                    dados_localidade = resultados[resultados[chave_agrupamento] == localidade_id]
                    dados_localidade = dados_localidade.sort_values('ano_mes', ascending=False)
                    
                    # Buscar último valor não zerado desta localidade
                    for _, row in dados_localidade.iterrows():
                        valor = row.iloc[8]  # Coluna I
                        if pd.notna(valor):
                            try:
                                valor_float = float(valor)
                                if valor_float > 0:
                                    total += valor_float
                                    break  # Só o último valor não zerado desta localidade
                            except (ValueError, TypeError):
                                continue
            else:
                # Fallback: buscar último valor geral
                resultados = resultados.sort_values('ano_mes', ascending=False)
                for _, row in resultados.iterrows():
                    valor = row.iloc[8]  # Coluna I
                    if pd.notna(valor):
                        try:
                            valor_float = float(valor)
                            if valor_float > 0:
                                total = valor_float
                                break
                        except (ValueError, TypeError):
                            continue
            
            return total
            
        except Exception as e:
            print(f"Erro ao buscar valor para código {codigo_sigis}: {e}")
            return 0
    
    hidrometros_data = []
    
    # Verificar se há dados reais disponíveis
    tem_dados_reais = False
    for ano in range(16):
        qtd_real = buscar_valor_agregado(codigos_hidrometros[ano])
        if qtd_real > 0:
            tem_dados_reais = True
            break
    
    # Se não há dados reais, retornar DataFrame vazio
    if not tem_dados_reais:
        return pd.DataFrame()
    
    for ano in range(16):
        # Buscar apenas dados reais
        qtd_hidrometros = buscar_valor_agregado(codigos_hidrometros[ano])
        volume_micromedido_sigis = buscar_valor_agregado(codigos_volume[ano])
        
        # Se não há dados reais, pular este ano
        if qtd_hidrometros == 0:
            continue
        
        volume_micromedido = volume_micromedido_sigis
        idm = idm_values[ano]
        
        # Fórmula corrigida: Vol. Submedido = (Vol. Micromedido / IDM) - Vol. Micromedido
        volume_submedido_base = volume_micromedido / (idm / 100) if idm > 0 else 0
        volume_submedido = volume_submedido_base - volume_micromedido
        
        media_por_hidrometro = volume_submedido / qtd_hidrometros if qtd_hidrometros > 0 else 0
        
        hidrometros_data.append({
            'Ano': ano,
            'Quantidade de Hidrômetros': int(qtd_hidrometros),
            'Volume Micromedido Período (m³)': volume_micromedido,
            'IDM': f"{idm:.2f}%".replace(".", ","),
            'Volume Submedido (m³)': volume_submedido,
            'Média por Hidrômetro': media_por_hidrometro
        })
    
    return pd.DataFrame(hidrometros_data)

def create_analysis_table(df_filtered, df_sigis, data_range):
    analysis_data = []
    if df_filtered.empty: return pd.DataFrame()
    
    grupos = [(loc, df_filtered[df_filtered['nome_localidade'] == loc]) for loc in df_filtered['nome_localidade'].unique()]
    volume_total_geral = df_filtered[df_filtered['nome_info'] == 'Volume de Entrada']['valor'].sum()
    
    for localidade_nome, df_grupo in grupos:
        if df_grupo.empty: continue
        
        try:
            volume_entrada = float(df_grupo[df_grupo['nome_info'] == 'Volume de Entrada']['valor'].sum())
            perdas_totais = float(df_grupo[df_grupo['nome_info'] == 'Volume de Perdas']['valor'].sum())
            perdas_reais = float(df_grupo[df_grupo['nome_info'] == 'Perdas Reais']['valor'].sum())
            
            if volume_entrada > 0:
                perc_perdas = (perdas_totais / volume_entrada) * 100
                
                # Obter códigos de localidade para busca no SIGIS
                localidades_filtradas = set(df_grupo['cod_localidade'].unique()) if 'cod_localidade' in df_grupo.columns else None
                
                # Calcular categoria e IVI usando a função unificada
                categoria, ivi, prac, prai = calcular_ivi(perdas_reais, volume_entrada, df_sigis, data_range, localidades_filtradas)
                ipl = calcular_ipl(df_sigis, data_range, localidades_filtradas)
                impacto_total = (volume_entrada / float(volume_total_geral)) * 100 if volume_total_geral > 0 else 0
                
                analysis_data.append({
                    'Regional': df_grupo['nome_regional'].iloc[0],
                    'Municipio': df_grupo['nome_municipio'].iloc[0],
                    'Localidade': localidade_nome,
                    'Categoria': categoria,
                    'Volume Total de entrada': volume_entrada,
                    '% de Impacto': impacto_total,
                    '% de perdas': perc_perdas,
                    'IPL': ipl,
                    'IVI': ivi
                })
        except (ValueError, TypeError) as e:
            print(f"Erro ao processar localidade {localidade_nome}: {e}")
            continue
    
    return pd.DataFrame(analysis_data)

def format_hierarchical_name(row):
    nivel_num = int(row['nivel_info'].split(' ')[1]) if 'nivel_info' in row and isinstance(row['nivel_info'], str) else 1
    nome = row['nome_info']
    itens_destaque = ['Perdas Aparentes', 'Perdas Reais', 'Consumo Autorizado Faturado', 'Autorizado não Faturado']
    
    if row['parent'] == "": return nome, "bold", 0
    elif nivel_num == 2: return nome, "bold", 1
    elif nome in itens_destaque: return nome, "subtle", nivel_num - 1
    else: return nome, "normal", max(0, nivel_num - 1)

def calculate_parent_percentage(df):
    df_copy = df.copy()
    df_copy['percentual_pai'] = 0.0
    valor_por_id = dict(zip(df_copy['id'], df_copy['valor']))
    
    for idx, row in df_copy.iterrows():
        if row['parent'] == "":
            df_copy.at[idx, 'percentual_pai'] = 100.0
        else:
            parent_id = row['parent']
            if parent_id in valor_por_id:
                parent_valor = valor_por_id[parent_id]
                if parent_valor > 0:
                    df_copy.at[idx, 'percentual_pai'] = (row['valor'] / parent_valor) * 100
    return df_copy

def create_hierarchical_display(df):
    df_copy = df.copy().sort_values('id').reset_index(drop=True)
    df_copy = calculate_parent_percentage(df_copy)
    hierarchy_info = df_copy.apply(format_hierarchical_name, axis=1)
    df_copy['nome_display'] = [info[0] for info in hierarchy_info]
    df_copy['style_type'] = [info[1] for info in hierarchy_info]
    df_copy['indent_level'] = [info[2] for info in hierarchy_info]
    return df_copy

def create_sortable_analysis_table(df_analysis):
    """Cria uma tabela de análise com opções de classificação"""
    if df_analysis.empty:
        return None, None
    
    # Preparar dados para classificação
    df_sort = df_analysis.copy()
    
    # Opções de classificação
    sort_options = {
        'Regional': 'Regional',
        'Município': 'Municipio',
        'Localidade': 'Localidade',
        'Categoria': 'Categoria',
        'Volume Total (m³)': 'Volume Total de entrada',
        '% de Impacto': '% de Impacto',
        '% de Perdas': '% de perdas',
        'IPL': 'IPL',
        'IVI': 'IVI'
    }
    
    # Controles de classificação
    col_sort1, col_sort2 = st.columns(2)
    
    with col_sort1:
        sort_column = st.selectbox(
            "🔽 Classificar por:",
            options=list(sort_options.keys()),
            index=2,  # Default: Localidade (índice 2)
            key="sort_column_analysis"
        )
    
    with col_sort2:
        sort_order = st.selectbox(
            "📊 Ordem:",
            options=["Crescente", "Decrescente"],
            index=0,  # Default: Crescente
            key="sort_order_analysis"
        )
    
    # Aplicar classificação
    column_to_sort = sort_options[sort_column]
    ascending = sort_order == "Crescente"
    
    # Tratamento especial para categoria (ordem lógica A, B, C, D)
    if column_to_sort == 'Categoria':
        categoria_order = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
        df_sort['categoria_num'] = df_sort['Categoria'].map(categoria_order)
        df_sort = df_sort.sort_values('categoria_num', ascending=ascending)
        df_sort = df_sort.drop('categoria_num', axis=1)
    else:
        df_sort = df_sort.sort_values(column_to_sort, ascending=ascending)
    
    # Preparar dados formatados para exibição
    df_display = df_sort.copy()
    df_display.insert(0, '#', range(1, len(df_display) + 1))
    
    # Aplicar formatação brasileira nas colunas numéricas
    df_display['Volume Total de entrada'] = df_display['Volume Total de entrada'].apply(lambda x: format_number_br(x, 2))
    df_display['% de Impacto'] = df_display['% de Impacto'].apply(lambda x: f"{x:.2f}%".replace(".", ","))
    df_display['% de perdas'] = df_display['% de perdas'].apply(lambda x: f"{x:.2f}%".replace(".", ","))
    df_display['IPL'] = df_display['IPL'].apply(lambda x: f"{x:.2f}".replace(".", ",") if x > 0 else "N/A")
    df_display['IVI'] = df_display['IVI'].apply(lambda x: f"{x:.2f}".replace(".", ",") if isinstance(x, (int, float)) and not pd.isna(x) and x > 0 else "N/A")
    
    return df_display, df_sort

# Interface principal
st.title("💧 Dashboard de Balanço Hídrico")

with st.sidebar:
    st.markdown("#### 📁 Carregamento de Dados")
    if 'file_loaded' not in st.session_state:
        st.session_state.file_loaded = False
    
    # Só mostrar carregamento se não há arquivo carregado
    if not st.session_state.file_loaded:        
        uploaded_file = st.file_uploader(
            "📊 **Arquivo Excel**",
            type=['xlsx', 'xls'],
            help="Arquivo Excel com duas planilhas:\n- Planilha 1: Dados do Balanço Hídrico\n- Planilha 2: Dados do SIGIS"
        )
        
        if uploaded_file is None:
            st.info("💡 **Nenhum arquivo carregado**\n\nFaça upload do seu arquivo Excel para começar a análise.")
            st.stop()  # Para a execução aqui se não há arquivo
        
        # Carregar dados
        df, df_sigis = load_data(uploaded_file)
        
        if df is None:
            st.error("❌ **Erro ao processar o arquivo**\n\nVerifique se o arquivo está no formato correto.")
            st.stop()
        
        # Marcar como carregado e salvar no session_state
        st.session_state.file_loaded = True
        st.session_state.df = df
        st.session_state.df_sigis = df_sigis
        st.session_state.uploaded_file = uploaded_file
        st.rerun()  # Recarregar a página para esconder o carregamento
    
    else:
        # Arquivo já carregado - recuperar do session_state
        df = st.session_state.df
        df_sigis = st.session_state.df_sigis
        
        # Mostrar apenas um pequeno indicador de que há arquivo carregado
        with st.expander("📊 Arquivo Carregado", expanded=False):
            st.success("✅ Arquivo Excel carregado com sucesso!")
            if st.button("Carregar Novo Arquivo"):
                # Limpar session_state para permitir novo carregamento
                st.session_state.file_loaded = False
                if 'df' in st.session_state:
                    del st.session_state.df
                if 'df_sigis' in st.session_state:
                    del st.session_state.df_sigis
                if 'uploaded_file' in st.session_state:
                    del st.session_state.uploaded_file
                st.rerun()
    
    st.header("🔍 Filtros")
    
    # Regional
    regional_selecionada = st.selectbox(
        "Regional:",
        ["Todas"] + sorted(df['nome_regional'].unique()),
        index=0,
        key="sidebar_regional"
    )
    
    # Município
    municipios_filtrados = sorted(df[df['nome_regional'] == regional_selecionada]['nome_municipio'].unique()) if regional_selecionada != "Todas" else sorted(df['nome_municipio'].unique())
    municipio_selecionado = st.selectbox(
        "Município:",
        ["Todos"] + municipios_filtrados,
        index=0,
        key="sidebar_municipio"
    )
    
    # Localidade
    if municipio_selecionado != "Todos":
        localidades_filtradas = sorted(df[df['nome_municipio'] == municipio_selecionado]['nome_localidade'].unique())
    elif regional_selecionada != "Todas":
        localidades_filtradas = sorted(df[df['nome_regional'] == regional_selecionada]['nome_localidade'].unique())
    else:
        localidades_filtradas = sorted(df['nome_localidade'].unique())
    localidade_selecionada = st.selectbox(
        "Localidade:",
        ["Todas"] + localidades_filtradas,
        index=0,
        key="sidebar_localidade"
    )
    
    # Período
    min_data, max_data = int(df['ano_mes'].min()), int(df['ano_mes'].max())
    
    # Criar opções formatadas para o slider
    periodo_options = []
    for ano_mes in range(min_data, max_data + 1):
        periodo_options.append((ano_mes, format_ano_mes(ano_mes)))
    
    # Mostrar slider com valores formatados
    data_range_indices = st.select_slider(
        "Período:",
        options=[opt[0] for opt in periodo_options],
        value=(min_data, max_data),
        format_func=lambda x: format_ano_mes(x),
        key="sidebar_periodo"
    )
    
    # Se o retorno for um único valor, converter para tupla
    if isinstance(data_range_indices, int):
        data_range = (data_range_indices, data_range_indices)
    else:
        data_range = data_range_indices

# ==========================================
# DEFINIR VARIÁVEIS GLOBAIS APÓS SIDEBAR
# ==========================================

# Garantir que data_range está disponível globalmente
if isinstance(st.session_state.sidebar_periodo, int):
    data_range = (st.session_state.sidebar_periodo, st.session_state.sidebar_periodo)
else:
    data_range = st.session_state.sidebar_periodo

# Garantir que outras variáveis estão disponíveis globalmente
regional_selecionada = st.session_state.sidebar_regional
municipio_selecionado = st.session_state.sidebar_municipio
localidade_selecionada = st.session_state.sidebar_localidade
        
st.markdown("---")

# Aplicar filtros
df_data_filtered = df[(df['ano_mes'] >= data_range[0]) & (df['ano_mes'] <= data_range[1])]
df_filtered, nivel_agregacao = apply_hierarchical_filters(df_data_filtered, regional_selecionada, municipio_selecionado, localidade_selecionada)

if df_filtered.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

# Agregar dados
df_aggregated = df_filtered.groupby(['id', 'parent', 'nome_info', 'nivel_info'], dropna=False).agg({
    'valor': 'sum', 'valor_acum': 'sum', 'cod_regional': 'first', 'nome_regional': 'first',
    'cod_municipio': 'first', 'nome_municipio': 'first', 'cod_localidade': 'first', 'nome_localidade': 'first', 'ano_mes': 'first'
}).reset_index()

df_aggregated['parent'] = df_aggregated['parent'].fillna("").astype(str).replace('nan', '')

# Contexto - Incluir período formatado
periodo_inicio = format_ano_mes(data_range[0])
periodo_fim = format_ano_mes(data_range[1])
periodo_texto = f"{periodo_inicio} a {periodo_fim}" if data_range[0] != data_range[1] else periodo_inicio

contextos = {
    "localidade": f"Localidade: {localidade_selecionada} | Período: {periodo_texto}", 
    "municipio": f"Município: {municipio_selecionado} | Período: {periodo_texto}", 
    "regional": f"Regional: {regional_selecionada} | Período: {periodo_texto}", 
    "geral": f"Todas as Regionais, Municípios e Localidades | Período: {periodo_texto}"
}
st.info(f"📍 **Dados exibidos para:** {contextos[nivel_agregacao]}")

# Calcular valores para análise
volume_total = df_aggregated[df_aggregated['nome_info'] == 'Volume de Entrada']['valor'].sum()
perdas_agua = df_aggregated[df_aggregated['nome_info'] == 'Volume de Perdas']['valor'].sum()
perdas_reais = df_aggregated[df_aggregated['nome_info'] == 'Perdas Reais']['valor'].sum()

# Obter localidades filtradas para busca no SIGIS
localidades_filtradas_sigis = set(df_filtered['cod_localidade'].unique()) if 'cod_localidade' in df_filtered.columns else None

categoria_perdas, ivi_calculado, prac_calculado, prai_calculado = calcular_ivi(
    perdas_reais, 
    volume_total, 
    df_sigis, 
    data_range, 
    localidades_filtradas_sigis
)

ipl_calculado = calcular_ipl(df_sigis, data_range, localidades_filtradas_sigis)
matriz_dados = get_matriz_banco_mundial()

# Indicadores Principais
st.subheader("Indicadores Principais")

if categoria_perdas != 'N/A':
    col_ind1, col_ind2, col_ind3, col_ind4 = st.columns([1, 1, 1, 4])
    
    with col_ind1:
        st.metric("Volume de Entrada", format_number_br(volume_total), help="Volume total de água que entra no sistema (m³)")
    
    with col_ind2:
        percentual_perdas = (perdas_agua/volume_total)*100 if volume_total > 0 else 0
        st.metric("% de Perdas", f"{percentual_perdas:.1f}%".replace(".", ","), help="Percentual de perdas em relação ao volume total")
    
    with col_ind3:
        if ipl_calculado > 0:
             st.metric("IPL", f"{ipl_calculado:.2f}".replace(".", ","), help="Índice de Perdas por Ligação (L/ligação/dia)")
        else:
            st.metric("IPL", "N/A", help="Dados insuficientes no SIGIS para calcular IPL")
    
    with col_ind4:
        ivi_formatado = f"{ivi_calculado:.2f}".replace(".", ",") if isinstance(ivi_calculado, (int, float)) and not pd.isna(ivi_calculado) and ivi_calculado > 0 else "N/A"
        
        # Definir cor da fonte baseada na categoria
        cor_fonte = "black" if categoria_perdas == "B" else "white"
        
        st.markdown(f"""
        <div style='display: flex; align-items: stretch; height: 80px;'>
            <div style='background: linear-gradient(135deg, {cores_categoria[categoria_perdas]}, {cores_categoria[categoria_perdas]}dd); 
                        color: {cor_fonte}; padding: 15px 25px; border-radius: 12px; text-align: center; 
                        display: flex; flex-direction: column; justify-content: center; min-width: 250px; margin-right: 15px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
                <h1 style='margin: 0; font-size: 1.8em; font-weight: bold; color: {cor_fonte}; line-height: 0.5;'>Categoria {categoria_perdas}</h1>
                <div style='margin-top: 2px; font-size: 0.85em; opacity: 0.9; color: {cor_fonte}; display: flex; justify-content: space-between;'>
                    <span>IVI: {ivi_formatado}</span>
                    <span>Pressão: 30m</span>
                </div>
            </div>
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 12px; flex: 1; 
                        display: flex; align-items: center; border-left: 4px solid {cores_categoria[categoria_perdas]};'>
                <p style='margin: 0; font-size: 18px; line-height: 1.3; color: #495057;'>
                    {matriz_dados['categorias'][categoria_perdas]['descricao']}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning("⚠️ Não há dados suficientes no SIGIS para calcular indicadores de performance.")

st.markdown("---")

# Recomendações
if categoria_perdas != 'N/A':
    recomendacoes = matriz_dados['recomendacoes'][categoria_perdas]

    # Definir cor da fonte baseada na categoria
    cor_fonte_titulo = "black" if categoria_perdas == "B" else cores_categoria[categoria_perdas]

    st.markdown(f"""
    <div style='background: linear-gradient(90deg, {cores_categoria[categoria_perdas]}22, {cores_categoria[categoria_perdas]}11); 
                padding: 1px 0px 0px 10px; border-radius: 10px; border-left: 4px solid {cores_categoria[categoria_perdas]};'>
        <h4 style='color: {cor_fonte_titulo}; margin-top: 5px; margin-bottom: 10px'>
            Ações Recomendadas para Categoria {categoria_perdas}
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    for i, rec in enumerate(recomendacoes, 1):
        with st.expander(f"**{i}.** {rec['titulo']}", expanded=False):
            for subtopico in rec['subtopicos']:
                st.markdown(f"• {subtopico}")

    st.markdown("<br>", unsafe_allow_html=True)  # Adiciona espaço extra

# Seção de Perdas Aceitáveis por Pressão
with st.expander("📊 Perdas Aceitáveis por Pressão (Litros/ligação/dia)", expanded=False):
    st.markdown("### Matriz de Perdas por Pressão - Banco Mundial")
    pressoes_df = pd.DataFrame(matriz_dados['perdas_por_pressao']).T
    
    html_pressao = "<table style='width: 100%; border-collapse: collapse; margin: 20px 0;'>"
    html_pressao += "<thead>"
    html_pressao += "<tr>"
    html_pressao += "<th rowspan='6' style='padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold; background-color: #f8f9fa; vertical-align: middle; width: 120px; min-width: 120px; max-width: 120px;'>Categoria de Desempenho Técnico</th>"
    html_pressao += "<th rowspan='2' style='padding: 15px; border: 1px solid #ddd; text-align: center; font-weight: bold; background-color: #f8f9fa; vertical-align: small; width: 150px; min-width: 150px; max-width: 150px;'>IVI <br> (Índice de Vazamento da Infraestrutura)</th>"
    html_pressao += "<th colspan='5' style='padding: 15px; border: 1px solid #ddd; text-align: center; font-weight: bold; background-color: #f8f9fa;'>Litros/ramal/dia<br>quando o sistema está pressurizado a uma pressão de:</th>"
    html_pressao += "</tr>"
    html_pressao += "<tr>"
    for pressao in ['10 m', '20 m', '30 m', '40 m', '50 m']:
        html_pressao += f"<th style='padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; background-color: #f8f9fa;'>{pressao}</th>"
    html_pressao += "</tr>"
    html_pressao += "</thead><tbody>"
    
    # Definir limites IVI por categoria
    ivi_limites = {'A': '1-4', 'B': '4-8', 'C': '8-16', 'D': '> 16'}
    
    for cat in ['A', 'B', 'C', 'D']:
        cor_categoria = cores_categoria[cat]
        html_pressao += f"<tr>"
        html_pressao += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold; background-color: {cor_categoria}; color: white; width: 60px; min-width: 60px; max-width: 60px;'>{cat}</td>"
        html_pressao += f"<td style='padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold;'>{ivi_limites[cat]}</td>"
        
        for pressao in pressoes_df.index:
            valor = pressoes_df.loc[pressao, cat]
            html_pressao += f"<td style='padding: 12px; border: 1px solid #ddd; text-align: center; font-size: 14px;'>{valor}</td>"
        html_pressao += "</tr>"
    
    html_pressao += "</tbody></table>"
    st.markdown(html_pressao, unsafe_allow_html=True)
    st.caption("Fonte: Banco Mundial (Lambert, 2008)")
    
st.markdown("---") 

# Gráficos
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Visão Hierárquica")
    
    if not df_aggregated.empty:
        NOMES_ABREVIADOS = {'Volume de Entrada': 'Vol. Entrada', 'Consumo Autorizado': 'Consumo Autor.', 'Consumo Autorizado Faturado': 'Consumo Fatur.', 'Volume Medido': 'Vol. Medido', 'Autorizado não Faturado': 'Não Faturado', 'Uso Operacional': 'Operacional', 'Uso Emergencial': 'Emergencial', 'Uso Social': 'Social', 'Volume de Perdas': 'Vol. Perdas', 'Perdas Aparentes': 'Perdas Apar.', 'Clandestinos': 'Clandestinos', 'Fraudes': 'Fraudes', 'Submedição': 'Submedição', 'Perdas Reais': 'Perdas Reais', 'Vazamento em Ramais': 'Vaz. Ramais', 'Outros Vazamentos': 'Outros Vaz.'}
        
        sunburst_data = []
        colors_list = []
        
        for _, row in df_aggregated.iterrows():
            # Converter valores para float
            try:
                valor_row = float(row['valor']) if row['valor'] != '' else 0
                volume_total_float = float(volume_total) if volume_total != '' else 0
            except (ValueError, TypeError):
                valor_row = 0
                volume_total_float = 0
            
            percentual = (valor_row / volume_total_float * 100) if volume_total_float > 0 else 0
            nome_abrev = NOMES_ABREVIADOS.get(row['nome_info'], row['nome_info'])
            percentual_formatted = f"{percentual:.1f}%".replace(".", ",")
            
            sunburst_data.append({
                'ids': row['id'], 'labels': f"{nome_abrev}<br>{percentual_formatted}",
                'parents': row['parent'], 'values': row['valor'], 'customdata': row['nome_info']
            })
            colors_list.append(CORES_PERSONALIZADAS.get(row['nome_info'], 'rgba(128, 128, 128, 0.7)'))
        
        sunburst_df = pd.DataFrame(sunburst_data)
        
        # Calcular percentuais relativos para cada item
        df_hierarchical_calc = df_aggregated.copy()
        df_hierarchical_calc = calculate_parent_percentage(df_hierarchical_calc)
        
        # Criar dados customizados com percentuais relativos
        custom_data_enhanced = []
        for _, row in df_aggregated.iterrows():
            # Buscar percentual relativo correspondente
            percentual_relativo = df_hierarchical_calc[df_hierarchical_calc['id'] == row['id']]['percentual_pai'].iloc[0]
            custom_data_enhanced.append([
                row['nome_info'],
                row['valor'],
                (row['valor'] / volume_total * 100) if volume_total > 0 else 0,
                percentual_relativo
            ])
        
        fig_sunburst = go.Figure(go.Sunburst(
            ids=sunburst_df['ids'], 
            labels=sunburst_df['labels'], 
            parents=sunburst_df['parents'],
            values=sunburst_df['values'], 
            customdata=custom_data_enhanced, 
            branchvalues="total",
            hovertemplate=(
                '<b>%{customdata[0]}</b><br>' +
                'Valor: %{customdata[1]:,.0f} m³<br>' +
                'Percentual do Total: %{customdata[2]:.1f}%<br>' +
                'Percentual Relativo: %{customdata[3]:.1f}%<br>' +
                '<extra></extra>'
            ),
            maxdepth=4, 
            insidetextorientation='horizontal',
            marker=dict(colors=colors_list, line=dict(color="white", width=1)),
            textfont=dict(size=16, color="black", family="Arial")
        ))
        
        fig_sunburst.update_layout(font_size=16, height=800, margin=dict(t=20, l=20, r=20, b=20))
        st.plotly_chart(fig_sunburst, use_container_width=True)

with col2:
    st.subheader(" ")
    
    if not df_aggregated.empty:
        df_hierarchical = create_hierarchical_display(df_aggregated)
        df_display = df_hierarchical.copy()
        df_display['Valor (m³)'] = df_display['valor'].apply(lambda x: format_number_br(x))
        df_display['Percentual'] = df_display['valor'].apply(lambda x: f"{(x/volume_total)*100:.1f}%".replace(".", ",") if volume_total > 0 else "0,0%")
        df_display['Percentual Pai'] = df_display['percentual_pai'].apply(lambda x: f"{x:.1f}%".replace(".", ","))
        
        num_rows = len(df_display)
        dynamic_height = min(100, max(400, (num_rows * 40) + 90))
        
        html_table = f"<div style='height: {dynamic_height}px; border: none; padding: 15px; font-family: Arial, sans-serif; overflow: visible;'>"
        html_table += "<table style='width: 100%; border-collapse: collapse;'>"
        html_table += "<thead style='background-color: #f0f2f6;'><tr>"
        html_table += "<th style='padding: 15px; text-align: left; border-bottom: 2px solid #ddd; font-weight: bold; font-size: 14px;'>Informação</th>"
        html_table += "<th style='padding: 15px; text-align: right; border-bottom: 2px solid #ddd; font-weight: bold; font-size: 14px;'>Valor (m³)</th>"
        html_table += "<th style='padding: 15px; text-align: right; border-bottom: 2px solid #ddd; font-weight: bold; font-size: 14px;'>% Total</th>"
        html_table += "<th style='padding: 15px; text-align: right; border-bottom: 2px solid #ddd; font-weight: bold; font-size: 14px;'>% Relativo</th></tr></thead><tbody>"
        
        for _, row in df_display.iterrows():
            indent = "&nbsp;" * (row['indent_level'] * 6)
            
            if row['style_type'] == "bold":
                nome_formatado = f"{indent}<strong>{row['nome_display']}</strong>"
                style_extra = "font-weight: bold; background-color: #f8f9fa; font-size: 13px;"
            elif row['style_type'] == "subtle":
                nome_formatado = f"{indent}{row['nome_display']}"
                style_extra = "background-color: #fafbfc; color: #495057; font-weight: 500; font-size: 13px;"
            else:
                nome_formatado = f"{indent}{row['nome_display']}"
                style_extra = "font-size: 12px;"
            
            html_table += f"<tr style='border-bottom: 1px solid #eee; {style_extra}'>"
            html_table += f"<td style='padding: 12px; vertical-align: middle;'>{nome_formatado}</td>"
            html_table += f"<td style='padding: 12px; text-align: right; vertical-align: middle;'>{row['Valor (m³)']}</td>"
            html_table += f"<td style='padding: 12px; text-align: right; vertical-align: middle;'>{row['Percentual']}</td>"
            html_table += f"<td style='padding: 12px; text-align: right; vertical-align: middle;'>{row['Percentual Pai']}</td></tr>"
        
        html_table += "</tbody></table></div>"
        st.markdown(html_table, unsafe_allow_html=True)

st.markdown("---")

# Análise de Hidrômetros e Submedição
with st.expander("🔧 Análise de Hidrômetros e Submedição", expanded=False):
    st.markdown("### Análise por Idade dos Hidrômetros")
    st.caption(f"Dados baseados nos filtros aplicados - {contextos[nivel_agregacao]}")
    st.caption("IDM*: Índice de Desempenho da Medição")
    
    df_hidrometros = create_hidrometros_table(df_filtered, df_sigis, data_range, regional_selecionada, municipio_selecionado, localidade_selecionada)
    
    if not df_hidrometros.empty:
        # Preparar dados formatados para exibição
        df_hidro_display = df_hidrometros.copy()
        
        # Aplicar formatação brasileira nas colunas numéricas
        df_hidro_display['Quantidade de Hidrômetros'] = df_hidro_display['Quantidade de Hidrômetros'].apply(lambda x: format_number_br(x))
        df_hidro_display['Volume Micromedido Período (m³)'] = df_hidro_display['Volume Micromedido Período (m³)'].apply(lambda x: format_number_br(x, 2))
        df_hidro_display['Volume Submedido (m³)'] = df_hidro_display['Volume Submedido (m³)'].apply(lambda x: format_number_br(x, 2))
        df_hidro_display['Média por Hidrômetro'] = df_hidro_display['Média por Hidrômetro'].apply(lambda x: format_number_br(x, 2))
        
        # Calcular altura da tabela para mostrar todas as linhas
        num_linhas = len(df_hidro_display)
        altura_tabela = 60 + (num_linhas * 45) + 20  # Cabeçalho + linhas + margem
        
        # Criar tabela HTML para hidrômetros
        html_hidro = f"<div style='height: {altura_tabela}px;'>"
        html_hidro += "<table style='width: 100%; border-collapse: collapse; font-family: Arial, sans-serif;'>"
        html_hidro += "<thead style='background-color: #f8f9fa;'>"
        html_hidro += "<tr>"
        html_hidro += "<th style='padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; font-size: 14px;'>Idade (Ano)</th>"
        html_hidro += "<th style='padding: 12px; border: 1px solid #ddd; text-align: right; font-weight: bold; font-size: 14px;'>Qtd. Hidrômetros</th>"
        html_hidro += "<th style='padding: 12px; border: 1px solid #ddd; text-align: right; font-weight: bold; font-size: 14px;'>Vol. Micromedido (m³)</th>"
        html_hidro += "<th style='padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; font-size: 14px;'>IDM</th>"
        html_hidro += "<th style='padding: 12px; border: 1px solid #ddd; text-align: right; font-weight: bold; font-size: 14px;'>Vol. Submedido (m³)</th>"
        html_hidro += "<th style='padding: 12px; border: 1px solid #ddd; text-align: right; font-weight: bold; font-size: 14px;'>Média de Vol. Submedido/Hidrômetro</th>"
        html_hidro += "</tr></thead><tbody>"
        
        for idx, row in df_hidro_display.iterrows():
            html_hidro += "<tr style='border-bottom: 1px solid #eee;'>"
            html_hidro += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: center; font-size: 13px; font-weight: bold;'>{row['Ano']}</td>"
            html_hidro += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: right; font-size: 13px;'>{row['Quantidade de Hidrômetros']}</td>"
            html_hidro += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: right; font-size: 13px;'>{row['Volume Micromedido Período (m³)']}</td>"
            html_hidro += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: center; font-size: 13px;'>{row['IDM']}</td>"
            html_hidro += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: right; font-size: 13px;'>{row['Volume Submedido (m³)']}</td>"
            html_hidro += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: right; font-size: 13px;'>{row['Média por Hidrômetro']}</td>"
            html_hidro += "</tr>"
        
        html_hidro += "</tbody></table></div>"
        
        # Renderizar a tabela de hidrômetros
        st.markdown(html_hidro, unsafe_allow_html=True)
        
        st.markdown("#### 📈 Resumo da Análise de Hidrômetros")
        col_hidro1, col_hidro2, col_hidro3, col_hidro4, col_hidro5 = st.columns(5)
        
        # Usar dados originais para cálculos
        with col_hidro1:
            total_hidrometros = df_hidrometros['Quantidade de Hidrômetros'].sum()
            st.metric("Total de Hidrômetros", format_number_br(total_hidrometros))
        with col_hidro2:
            volume_total_micro = df_hidrometros['Volume Micromedido Período (m³)'].sum()
            st.metric("Vol. Total Micromedido", f"{format_number_br(volume_total_micro)} m³")
        with col_hidro3:
            volume_total_sub = df_hidrometros['Volume Submedido (m³)'].sum()
            st.metric("Vol. Total Submedido", f"{format_number_br(volume_total_sub)} m³")
        with col_hidro4:
            perda_submedicao = (volume_total_sub / (volume_total_micro + volume_total_sub)) * 100 if volume_total_micro > 0 else 0
            st.metric("% Perda por Submedição", f"{perda_submedicao:.1f}%".replace(".", ","))
        with col_hidro5:
            hidrometros_5_anos_mais = df_hidrometros[df_hidrometros['Ano'] >= 5]['Quantidade de Hidrômetros'].sum()
            st.metric("Hidrômetros ≥ 5 anos", format_number_br(hidrometros_5_anos_mais))

        # Adicionar nova linha com mais métricas
        st.markdown("#### 🎯 Análise de Prioridades")
        col_hidro6, col_hidro7, col_hidro8, col_hidro9, col_hidro10 = st.columns(5)
        
        with col_hidro6:
            # Calcular índice de prioridade combinando volume absoluto e média por hidrômetro
            df_hidrometros_calc = df_hidrometros.copy()
            
            # Normalizar volume absoluto (0-100)
            vol_sub_norm = (df_hidrometros_calc['Volume Submedido (m³)'] / df_hidrometros_calc['Volume Submedido (m³)'].max()) * 100
            
            # Normalizar média por hidrômetro (0-100)
            media_norm = (df_hidrometros_calc['Média por Hidrômetro'] / df_hidrometros_calc['Média por Hidrômetro'].max()) * 100
            
            # Índice de prioridade: 60% peso para volume absoluto + 40% peso para média por hidrômetro
            df_hidrometros_calc['Indice_Prioridade'] = (vol_sub_norm * 0.6) + (media_norm * 0.4)
            
            # Encontrar idade com maior índice de prioridade
            idx_maior_prioridade = df_hidrometros_calc['Indice_Prioridade'].idxmax()
            idade_prioridade = df_hidrometros_calc.loc[idx_maior_prioridade, 'Ano']
            vol_absoluto = df_hidrometros_calc.loc[idx_maior_prioridade, 'Volume Submedido (m³)']
            media_hidro = df_hidrometros_calc.loc[idx_maior_prioridade, 'Média por Hidrômetro']
            
            st.metric(
                "Prioridade de Troca", 
                f"Idade {idade_prioridade}",
                delta=f"{format_number_br(vol_absoluto, 0)} m³ total | {format_number_br(media_hidro, 1)} m³/hidro".replace(".", ","),
                help="Idade prioritária considerando volume total de submedição (60%) + média por hidrômetro (40%)"
            )
        
        with col_hidro7:
            # Percentual de hidrômetros com 5 anos ou mais
            perc_5_anos_mais = (hidrometros_5_anos_mais / total_hidrometros * 100) if total_hidrometros > 0 else 0
            st.metric("% ≥ 5 anos", f"{perc_5_anos_mais:.1f}%".replace(".", ","))
        
        with col_hidro8:
            # Volume submedido dos hidrômetros ≥ 5 anos
            vol_sub_5_anos = df_hidrometros[df_hidrometros['Ano'] >= 5]['Volume Submedido (m³)'].sum()
            st.metric("Vol. Submedido ≥ 5 anos", f"{format_number_br(vol_sub_5_anos)} m³")
        
        with col_hidro9:
            # Impacto percentual dos hidrômetros ≥ 5 anos na submedição total
            impacto_5_anos = (vol_sub_5_anos / volume_total_sub * 100) if volume_total_sub > 0 else 0
            st.metric("Impacto ≥ 5 anos", f"{impacto_5_anos:.1f}%".replace(".", ","))
        
        with col_hidro10:
            # Economia potencial se trocar hidrômetros ≥ 5 anos
            economia_potencial = vol_sub_5_anos * 0.7  # Assumindo 70% de redução na submedição
            st.metric("Economia Potencial", f"{format_number_br(economia_potencial)} m³")

                # Criar escala de cores compatível com a paleta do sunburst
        cores_personalizadas_grafico = [
            'rgba(16, 72, 97, 1)',      # Ano 0 - Azul escuro (similar ao Consumo Autorizado)
            'rgba(70, 130, 180, 1)',    # Ano 1 - Azul médio (similar ao Autorizado não Faturado)
            'rgba(131, 204, 235, 1)',   # Ano 2 - Azul claro (similar ao Consumo Autorizado Faturado)
            'rgba(192, 230, 245, 1)',   # Ano 3 - Azul muito claro (similar ao Volume Medido)
            'rgba(220, 240, 250, 1)',   # Ano 4 - Azul claríssimo
            'rgba(255, 235, 235, 1)',   # Ano 5 - Transição para vermelho muito claro
            'rgba(255, 217, 217, 1)',   # Ano 6 - Vermelho muito claro (similar aos usos)
            'rgba(255, 200, 200, 1)',   # Ano 7 - Vermelho claro
            'rgba(255, 180, 180, 1)',   # Ano 8 - Vermelho claro médio
            'rgba(255, 160, 160, 1)',   # Ano 9 - Vermelho médio claro
            'rgba(255, 140, 140, 1)',   # Ano 10 - Vermelho médio
            'rgba(200, 100, 100, 1)',   # Ano 11 - Vermelho médio escuro
            'rgba(165, 42, 42, 1)',     # Ano 12 - Vermelho escuro (similar às Perdas)
            'rgba(140, 30, 30, 1)',     # Ano 13 - Vermelho muito escuro
            'rgba(120, 0, 0, 1)',       # Ano 14 - Vermelho escuríssimo (similar ao Volume de Perdas)
            'rgba(100, 0, 0, 1)'        # Ano 15 - Vermelho final
        ]
        
        # Preparar dados para o gráfico com informações complementares
        df_grafico = df_hidrometros.copy()
        
        # Calcular percentuais em relação ao total
        total_hidrometros_graf = df_grafico['Quantidade de Hidrômetros'].sum()
        df_grafico['Percentual_Quantidade'] = (df_grafico['Quantidade de Hidrômetros'] / total_hidrometros_graf * 100).round(2)
        
        # Mapear cores aos anos
        df_grafico['Cor'] = df_grafico['Ano'].map(lambda x: cores_personalizadas_grafico[x])
        
        # Criar gráfico melhorado
        fig_hidro_qtd = go.Figure()
        
        fig_hidro_qtd.add_trace(go.Bar(
            x=df_grafico['Ano'],
            y=df_grafico['Quantidade de Hidrômetros'],
            marker_color=df_grafico['Cor'],
            hovertemplate=(
                '<b>Idade:</b> %{x} anos<br>' +
                '<b>Quantidade:</b> %{customdata[0]:,.0f} hidrômetros<br>' +
                '<b>Volume Micromedido:</b> %{customdata[1]:,.2f} m³<br>' +
                '<b>% em relação ao todo:</b> %{customdata[2]:.2f}%<br>' +
                '<extra></extra>'
            ),
            customdata=list(zip(
                df_grafico['Quantidade de Hidrômetros'],
                df_grafico['Volume Micromedido Período (m³)'],
                df_grafico['Percentual_Quantidade']
            )),
            showlegend=False
        ))
        
        fig_hidro_qtd.update_layout(
            title="Quantidade de Hidrômetros por Idade",
            xaxis_title="Idade (Anos)",
            yaxis_title="Quantidade de Hidrômetros",
            height=400,
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1,
                range=[-0.5, 15.5]
            ),
            yaxis=dict(
                tickformat=',',
                separatethousands=True
            ),
            hovermode='x'
        )
        
        st.plotly_chart(fig_hidro_qtd, use_container_width=True)
    else:
        st.warning("⚠️ Não há dados de hidrômetros disponíveis no SIGIS para os filtros selecionados.")

st.markdown("---") 

# Tabela de Análise Detalhada com Classificação
st.subheader("📊 Tabela de Análise Detalhada")
df_analysis = create_analysis_table(df_filtered, df_sigis, data_range)

if not df_analysis.empty:
    st.markdown("### Dados por Localidade")
    
    # Criar tabela com opções de classificação
    df_display_sorted, df_original_sorted = create_sortable_analysis_table(df_analysis)
    
    if df_display_sorted is not None:
        # Usar a estrutura de tabela HTML que já estava funcionando antes
        html_table = "<div style='max-height: 600px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px;'>"
        html_table += "<table style='width: 100%; border-collapse: collapse; font-family: Arial, sans-serif;'>"
        html_table += "<thead style='position: sticky; top: 0; background-color: #f8f9fa; z-index: 10;'>"
        html_table += "<tr>"
        html_table += "<th style='padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; font-size: 14px;'>#</th>"
        html_table += "<th style='padding: 12px; border: 1px solid #ddd; text-align: left; font-weight: bold; font-size: 14px;'>Regional</th>"
        html_table += "<th style='padding: 12px; border: 1px solid #ddd; text-align: left; font-weight: bold; font-size: 14px;'>Município</th>"
        html_table += "<th style='padding: 12px; border: 1px solid #ddd; text-align: left; font-weight: bold; font-size: 14px;'>Localidade</th>"
        html_table += "<th style='padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; font-size: 14px;'>Cat</th>"
        html_table += "<th style='padding: 12px; border: 1px solid #ddd; text-align: right; font-weight: bold; font-size: 14px;'>Volume Total (m³)</th>"
        html_table += "<th style='padding: 12px; border: 1px solid #ddd; text-align: right; font-weight: bold; font-size: 14px;'>% Impacto</th>"
        html_table += "<th style='padding: 12px; border: 1px solid #ddd; text-align: right; font-weight: bold; font-size: 14px;'>% Perdas</th>"
        html_table += "<th style='padding: 12px; border: 1px solid #ddd; text-align: right; font-weight: bold; font-size: 14px;'>IPL</th>"
        html_table += "<th style='padding: 12px; border: 1px solid #ddd; text-align: right; font-weight: bold; font-size: 14px;'>IVI</th>"
        html_table += "</tr></thead><tbody>"
        
        for idx, row in df_display_sorted.iterrows():
            categoria = row['Categoria']
            cor_categoria = cores_categoria_bg.get(categoria, 'rgba(128, 128, 128, 0.3)')
            
            html_table += "<tr style='border-bottom: 1px solid #eee;'>"
            html_table += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: center; font-size: 13px;'>{row['#']}</td>"
            html_table += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: left; font-size: 13px;'>{row['Regional']}</td>"
            html_table += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: left; font-size: 13px;'>{row['Municipio']}</td>"
            html_table += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: left; font-size: 13px;'>{row['Localidade']}</td>"
            html_table += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: center; font-size: 13px; background-color: {cor_categoria}; color: white; font-weight: bold;'>{categoria}</td>"
            html_table += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: right; font-size: 13px;'>{row['Volume Total de entrada']}</td>"
            html_table += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: right; font-size: 13px;'>{row['% de Impacto']}</td>"
            html_table += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: right; font-size: 13px;'>{row['% de perdas']}</td>"
            html_table += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: right; font-size: 13px;'>{row['IPL']}</td>"
            html_table += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: right; font-size: 13px;'>{row['IVI']}</td>"
            html_table += "</tr>"
        
        html_table += "</tbody></table></div>"
        
        # Renderizar a tabela
        st.markdown(html_table, unsafe_allow_html=True)
        
        # CONDIÇÃO: Só mostrar resumo e visualizações se houver mais de uma localidade
        num_localidades = len(df_analysis)
        if num_localidades > 1:
            st.markdown("<br>", unsafe_allow_html=True)  # Adiciona espaço extra
            st.markdown("### 📈 Resumo Estatístico")
            col_stats1, col_stats2, col_stats3 = st.columns(3)  # Reduzido de 5 para 3 colunas

            with col_stats1: 
                st.metric("Total de Localidades", len(df_analysis))
            with col_stats2: 
                categoria_counts = df_analysis['Categoria'].value_counts()
                st.metric("Categoria Predominante", categoria_counts.index[0] if not categoria_counts.empty else 'N/A')
            with col_stats3: 
                volume_total_analysis = df_analysis['Volume Total de entrada'].sum()
                st.metric("Volume Total", f"{format_number_br(volume_total_analysis)} m³")
            
            with st.expander("📊 Visualizações Complementares", expanded=False):
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    categoria_dist = df_analysis['Categoria'].value_counts()
                    fig_categoria = go.Figure(data=[go.Pie(
                        labels=list(categoria_dist.index),
                        values=list(categoria_dist.values),
                        marker_colors=[cores_classificacao.get(cat, "rgba(128, 128, 128, 0.5)") for cat in categoria_dist.index],
                        textposition='inside', 
                        textinfo='percent+label',
                        textfont=dict(size=16, color='black', family='Arial'),
                        hovertemplate='<b>Categoria %{label}</b><br>Localidades: %{value}<br>Percentual: %{percent}<extra></extra>'
                    )])
                    fig_categoria.update_layout(title="Distribuição por Categoria", height=350, showlegend=False)
                    st.plotly_chart(fig_categoria, use_container_width=True)
                
                with col_chart2:
                    df_analysis_scatter = df_analysis.copy()
                    df_analysis_scatter['IPL_size'] = df_analysis_scatter['IPL'].apply(lambda x: max(8, min(50, abs(x)/10)) if x > 0 else 8)
                    
                    fig_scatter = go.Figure()
                    
                    for categoria in df_analysis_scatter['Categoria'].unique():
                        df_cat = df_analysis_scatter[df_analysis_scatter['Categoria'] == categoria]
                        
                        fig_scatter.add_trace(go.Scatter(
                            x=df_cat['Volume Total de entrada'],
                            y=df_cat['% de perdas'],
                            mode='markers+text',
                            name=f'Categoria {categoria}',
                            marker=dict(
                                size=df_cat['IPL_size'],
                                color=cores_classificacao.get(categoria, "rgba(128, 128, 128, 0.5)"),
                                line=dict(width=1, color='white'),
                                sizemode='diameter'
                            ),
                            text=df_cat['Localidade'],
                            textposition='top center',
                            textfont=dict(size=10, color='black'),
                            hovertemplate=(
                                '<b>%{text}</b><br>' +
                                'Regional: %{customdata[0]}<br>' +
                                'Município: %{customdata[1]}<br>' +
                                'Volume Total: %{x:,.0f} m³<br>' +
                                '% Perdas: %{y:.1f}%<br>' +
                                'IPL: %{customdata[2]:.0f}<br>' +
                                'IVI: %{customdata[3]}<br>' +
                                'Categoria: %{customdata[4]}<br>' +
                                '<extra></extra>'
                            ),
                            customdata=list(zip(
                                df_cat['Regional'],
                                df_cat['Municipio'],
                                df_cat['IPL'],
                                df_cat['IVI'],
                                df_cat['Categoria']
                            ))
                        ))
                    
                    fig_scatter.update_layout(
                        title="Volume vs % Perdas",
                        xaxis_title="Volume Total de Entrada (m³)",
                        yaxis_title="% de Perdas",
                        height=350,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        xaxis=dict(tickformat=','),
                        yaxis=dict(tickformat='.1f')
                    )
                    
                    st.plotly_chart(fig_scatter, use_container_width=True)      

else:
    st.warning("⚠️ Não há dados suficientes para gerar a tabela de análise.")

# Nova seção: Evolução Temporal
st.write("---")

# Verificar se há dados suficientes para análise temporal
if df_sigis is not None and len(df['ano_mes'].unique()) > 1:
    
    # Obter todos os meses disponíveis no período filtrado
    meses_disponiveis = sorted(df_data_filtered['ano_mes'].unique())
    
    if len(meses_disponiveis) >= 3:  # Mínimo 3 meses para análise temporal
        
        # CALCULAR VALORES ACUMULADOS CORRETAMENTE
        dados_evolucao = []
        
        for i, mes_atual in enumerate(meses_disponiveis):
            # ACUMULAR desde o primeiro mês até o mês atual
            meses_acumulados = meses_disponiveis[:i+1]
            data_range_acumulado = (meses_acumulados[0], mes_atual)
            
            # Filtrar dados ACUMULADOS até o mês atual
            df_acumulado = df_data_filtered[df_data_filtered['ano_mes'].isin(meses_acumulados)]
            df_acumulado_filtered, _ = apply_hierarchical_filters(df_acumulado, regional_selecionada, municipio_selecionado, localidade_selecionada)
            
            if df_acumulado_filtered.empty:
                continue
            
            # Obter localidades para busca no SIGIS
            localidades_filtradas = None
            if not df_acumulado_filtered.empty:
                if 'cod_localidade' in df_acumulado_filtered.columns:
                    localidades_filtradas = list(set(df_acumulado_filtered['cod_localidade'].unique()))
                elif 'nome_localidade' in df_acumulado_filtered.columns:
                    localidades_filtradas = list(set(df_acumulado_filtered['nome_localidade'].unique()))
            
            # CALCULAR IPL USANDO VALORES ACUMULADOS
            # Replicar exatamente a função calcular_ipl com debug
            try:
                from datetime import datetime
                import calendar
                
                # Códigos SIGIS conforme documentação oficial
                codigo_producao = 1      # Volume Produzido de Água
                codigo_importado = 67    # Volume Importado
                codigo_exportado = 68    # Volume Exportado
                codigo_uso_op_1 = 29     # Descarga de rede
                codigo_uso_op_2 = 30     # Quebra de rede por terceiros
                codigo_uso_op_3 = 31     # Limpeza sanitária de reservatórios
                codigo_uso_op_4 = 32     # Utilização do corpo de bombeiros
                codigo_consumido = 9642  # Volume Consumido de água
                codigo_ligacoes = 9603   # Ligações reais de água faturadas
                
                # Buscar volumes do período ACUMULADO (soma)
                volume_producao = buscar_dados_sigis(df_sigis, codigo_producao, data_range_acumulado, localidades_filtradas)
                volume_importado = buscar_dados_sigis(df_sigis, codigo_importado, data_range_acumulado, localidades_filtradas)
                volume_exportado = buscar_dados_sigis(df_sigis, codigo_exportado, data_range_acumulado, localidades_filtradas)
                volume_uso_op_1 = buscar_dados_sigis(df_sigis, codigo_uso_op_1, data_range_acumulado, localidades_filtradas)
                volume_uso_op_2 = buscar_dados_sigis(df_sigis, codigo_uso_op_2, data_range_acumulado, localidades_filtradas)
                volume_uso_op_3 = buscar_dados_sigis(df_sigis, codigo_uso_op_3, data_range_acumulado, localidades_filtradas)
                volume_uso_op_4 = buscar_dados_sigis(df_sigis, codigo_uso_op_4, data_range_acumulado, localidades_filtradas)
                volume_consumido = buscar_dados_sigis(df_sigis, codigo_consumido, data_range_acumulado, localidades_filtradas)
                
                # Buscar ligações (último valor não zerado do período)
                ligacoes_reais = buscar_ultimo_valor_nao_zerado_simples(df_sigis, codigo_ligacoes, data_range_acumulado, localidades_filtradas)
                
                # Calcular número real de dias do período ACUMULADO
                data_inicio, data_fim = data_range_acumulado
                
                if data_inicio == data_fim:
                    # Mesmo mês - calcular dias do mês
                    ano = data_inicio // 100
                    mes = data_inicio % 100
                    dias_periodo = calendar.monthrange(ano, mes)[1]
                else:
                    # Períodos diferentes - calcular dias totais
                    ano_inicio = data_inicio // 100
                    mes_inicio = data_inicio % 100
                    ano_fim = data_fim // 100
                    mes_fim = data_fim % 100
                    
                    # Data de início (primeiro dia do mês inicial)
                    dt_inicio = datetime(ano_inicio, mes_inicio, 1)
                    
                    # Data de fim (último dia do mês final)
                    ultimo_dia_mes_fim = calendar.monthrange(ano_fim, mes_fim)[1]
                    dt_fim = datetime(ano_fim, mes_fim, ultimo_dia_mes_fim)
                    
                    # Calcular diferença em dias
                    diferenca = dt_fim - dt_inicio
                    dias_periodo = diferenca.days + 1  # +1 para incluir o último dia
                
                # Somar volumes operacionais
                volume_operacional_total = volume_uso_op_1 + volume_uso_op_2 + volume_uso_op_3 + volume_uso_op_4
                
                # Aplicar fórmula IPL
                numerador = volume_producao + volume_importado - volume_exportado - volume_operacional_total - volume_consumido
                denominador = ligacoes_reais * dias_periodo
                
                ipl_calculado = (1000 * numerador) / denominador if denominador > 0 else 0
                ipl_calculado = max(0, ipl_calculado)
                
                # Calcular dados do balanço hídrico ACUMULADO
                df_acumulado_agg = df_acumulado_filtered.groupby(['id', 'parent', 'nome_info', 'nivel_info'], dropna=False).agg({
                    'valor': 'sum', 'valor_acum': 'sum'
                }).reset_index()
                
                volume_entrada_bh = df_acumulado_agg[df_acumulado_agg['nome_info'] == 'Volume de Entrada']['valor'].sum()
                perdas_totais_bh = df_acumulado_agg[df_acumulado_agg['nome_info'] == 'Volume de Perdas']['valor'].sum()
                perdas_reais_bh = df_acumulado_agg[df_acumulado_agg['nome_info'] == 'Perdas Reais']['valor'].sum()
                
                perc_perdas_bh = (perdas_totais_bh / volume_entrada_bh) * 100 if volume_entrada_bh > 0 else 0
                
                # Calcular IVI usando valores acumulados
                categoria, ivi, prac, prai = calcular_ivi(perdas_reais_bh, volume_entrada_bh, df_sigis, data_range_acumulado, localidades_filtradas)
                
                dados_evolucao.append({
                    'ano_mes': mes_atual,
                    'ano_mes_formatted': format_ano_mes(mes_atual),
                    'periodo_acumulado': f"{format_ano_mes(data_range_acumulado[0])} a {format_ano_mes(data_range_acumulado[1])}",
                    'dias_periodo': dias_periodo,
                    'volume_producao': volume_producao,
                    'volume_importado': volume_importado,
                    'volume_exportado': volume_exportado,
                    'volume_operacional': volume_operacional_total,
                    'volume_consumido': volume_consumido,
                    'ligacoes_reais': ligacoes_reais,
                    'numerador_ipl': numerador,
                    'denominador_ipl': denominador,
                    'volume_entrada_bh': volume_entrada_bh,
                    'perdas_totais_bh': perdas_totais_bh,
                    'perdas_reais_bh': perdas_reais_bh,
                    'perc_perdas': perc_perdas_bh,
                    'ipl': ipl_calculado,
                    'ivi': ivi if isinstance(ivi, (int, float)) and not pd.isna(ivi) else 0,
                    'categoria': categoria
                })
                
            except Exception as e:
                st.write(f"Erro ao calcular IPL para {format_ano_mes(mes_atual)}: {e}")
                continue
        
        if len(dados_evolucao) >= 3:
            df_evolucao = pd.DataFrame(dados_evolucao)
            
            # Função para calcular tendência
            def calcular_tendencia(x, y, periodos_futuros):
                import numpy as np
                mask = ~(pd.isna(y) | (y == 0))
                if mask.sum() < 2:
                    return []
                
                x_valid = np.array(range(len(y)))[mask]
                y_valid = np.array(y)[mask]
                
                n = len(x_valid)
                sum_x = np.sum(x_valid)
                sum_y = np.sum(y_valid)
                sum_xy = np.sum(x_valid * y_valid)
                sum_x2 = np.sum(x_valid ** 2)
                
                denominador = n * sum_x2 - sum_x ** 2
                if denominador == 0:
                    return []
                
                a = (n * sum_xy - sum_x * sum_y) / denominador
                b = (sum_y - a * sum_x) / n
                
                tendencia = []
                for i in range(len(y), len(y) + periodos_futuros):
                    valor_projetado = a * i + b
                    tendencia.append(max(0, valor_projetado))
                
                return tendencia
            
            # Calcular tendências
            tendencia_ipl_6m = calcular_tendencia(range(len(df_evolucao)), df_evolucao['ipl'].tolist(), 6)
            tendencia_perdas_6m = calcular_tendencia(range(len(df_evolucao)), df_evolucao['perc_perdas'].tolist(), 6)
            
            # Gerar meses futuros
            ultimo_mes = df_evolucao['ano_mes'].iloc[-1]
            def gerar_meses_futuros(mes_base, qtd_meses):
                meses_futuros = []
                ano = mes_base // 100
                mes = mes_base % 100
                
                for i in range(1, qtd_meses + 1):
                    mes += 1
                    if mes > 12:
                        mes = 1
                        ano += 1
                    meses_futuros.append(ano * 100 + mes)
                
                return meses_futuros
            
            meses_futuros_6m = gerar_meses_futuros(ultimo_mes, 6)

            # Gráfico IPL
            st.markdown("<h4 style='margin-bottom: -10px;'>Evolução do IPL (Índice de Perdas por Ligação)</h4>", unsafe_allow_html=True)
            
            fig_ipl = go.Figure()
            
            # Filtrar apenas valores IPL > 0
            df_ipl_grafico = df_evolucao[df_evolucao['ipl'] > 0].copy()
            
            if not df_ipl_grafico.empty:
                fig_ipl.add_trace(go.Scatter(
                    x=df_ipl_grafico['ano_mes_formatted'],
                    y=df_ipl_grafico['ipl'],
                    mode='lines+markers+text',
                    name='IPL Real',
                    line=dict(color='#1e3a8a', width=4),
                    marker=dict(size=10, color='#1e3a8a', symbol='circle', 
                               line=dict(color='white', width=2)),
                    text=[f"{val:.1f}".replace(".", ",") for val in df_ipl_grafico['ipl']],
                    textposition="top center",
                    textfont=dict(size=16, color='#1e3a8a', family="Arial"),
                    hovertemplate='<b>%{x}</b><br>IPL: %{y:.2f} L/lig/dia<br><extra></extra>',
                    showlegend=True
                ))
                
                # Tendência
                if tendencia_ipl_6m:
                    meses_6m_formatted = [format_ano_mes(mes) for mes in meses_futuros_6m[:len(tendencia_ipl_6m)]]
                    fig_ipl.add_trace(go.Scatter(
                        x=meses_6m_formatted,
                        y=tendencia_ipl_6m,
                        mode='lines+markers+text',
                        name='Tendência',
                        line=dict(color='#4b5563', width=3, dash='dash'),
                        marker=dict(size=8, color='#4b5563', symbol='square'),
                        text=[f"{val:.1f}".replace(".", ",") for val in tendencia_ipl_6m],
                        textposition="top center",
                        textfont=dict(size=16, color='#4b5563', family="Arial"),
                        showlegend=True
                    ))
            
            # Linhas de referência
            fig_ipl.add_hline(y=150, line_dash="dot", line_color="#83CCEB", annotation_text="Cat. A (150)")
            fig_ipl.add_hline(y=300, line_dash="dot", line_color="#FFE07D", annotation_text="Cat. B (300)")
            fig_ipl.add_hline(y=600, line_dash="dot", line_color="#ED9283", annotation_text="Cat. C (600)")
            
            fig_ipl.update_layout(
                height=450,
                xaxis_title="Período",
                yaxis_title="IPL (Litros/ligação/dia)",
                hovermode='x unified',
                margin=dict(t=10, b=40, l=50, r=20)
            )
            
            st.plotly_chart(fig_ipl, use_container_width=True)

            # Gráfico % Perdas
            st.markdown("<h4 style='margin-bottom: -10px;'>Evolução das Perdas (Percentual)</h4>", unsafe_allow_html=True)

            # Criar a figura primeiro
            fig_perdas = go.Figure()

            # 1. PRIMEIRO: Adicionar faixas coloridas de fundo
            fig_perdas.add_hrect(
                y0=0, y1=15,
                fillcolor="rgba(131, 204, 235, 0.05)",
                layer="below",
                line_width=0
            )

            fig_perdas.add_hrect(
                y0=15, y1=25,
                fillcolor="rgba(255, 224, 125, 0.1)",
                layer="below",
                line_width=0
            )

            fig_perdas.add_hrect(
                y0=25, y1=50,
                fillcolor="rgba(237, 146, 131, 0.05)",
                layer="below",
                line_width=0
            )

            # NOVA FAIXA: Crítico (acima de 50%)
            fig_perdas.add_hrect(
                y0=50, y1=100,
                fillcolor="rgba(139, 0, 0, 0.07)",
                layer="below",
                line_width=0
            )

            # 2. SEGUNDO: Adicionar linhas de referência
            fig_perdas.add_hline(
                y=15, 
                line_dash="dot", 
                line_color="rgba(131, 204, 235, 0.8)", 
                line_width=2,
                annotation_text="Desejável (≤15%)",
                annotation_position="right",
                annotation_font_color="#104861",  
                annotation_font_size=12,                           
                annotation_font_family="Arial"                     
            )

            fig_perdas.add_hline(
                y=25, 
                line_dash="dot", 
                line_color="rgba(255, 224, 125, 0.8)", 
                line_width=2,
                annotation_text="Aceitável (15-25%)",
                annotation_position="right",
                annotation_font_color="#B8860B",  
                annotation_font_size=12,                           
                annotation_font_family="Arial"   
            )

            fig_perdas.add_hline(
                y=35,
                line_dash="dot", 
                line_color="rgba(237, 146, 131, 0.0)",
                line_width=0,
                annotation_text="Não Aceitável (25-50%)",
                annotation_position="right",
                annotation_font_color="#8B0000",  
                annotation_font_size=12,                           
                annotation_font_family="Arial"   
            )

            fig_perdas.add_hline(
                y=50, 
                line_dash="dot", 
                line_color="rgba(139, 0, 0, 0.8)",
                line_width=2,
                annotation_text="Crítico (>50%)",
                annotation_position="right",
                annotation_font_color="#720505",  
                annotation_font_size=12,                           
                annotation_font_family="Arial"   
            )

            # 3. TERCEIRO: Adicionar os dados principais
            fig_perdas.add_trace(go.Scatter(
                x=df_evolucao['ano_mes_formatted'],
                y=df_evolucao['perc_perdas'],
                mode='lines+markers+text',
                name='% Perdas Real',
                line=dict(color='#1e3a8a', width=4),
                marker=dict(size=10, color='#1e3a8a', symbol='circle'),
                text=[f"{val:.1f}%".replace(".", ",") for val in df_evolucao['perc_perdas']],
                textposition="top center",
                textfont=dict(size=16, color='#1e3a8a', family="Arial"),
                showlegend=True
            ))

            # 4. QUARTO: Adicionar tendência
            if tendencia_perdas_6m:
                meses_6m_formatted = [format_ano_mes(mes) for mes in meses_futuros_6m[:len(tendencia_perdas_6m)]]
                fig_perdas.add_trace(go.Scatter(
                    x=meses_6m_formatted,
                    y=tendencia_perdas_6m,
                    mode='lines+markers+text',
                    name='Tendência',
                    line=dict(color='#4b5563', width=3, dash='dash'),
                    marker=dict(size=8, color='#4b5563', symbol='square'),
                    text=[f"{val:.1f}%".replace(".", ",") for val in tendencia_perdas_6m],
                    textposition="top center",
                    textfont=dict(size=16, color='#4b5563', family="Arial"),
                    showlegend=True
                ))

            fig_perdas.update_layout(
                height=450,
                xaxis_title="Período",
                yaxis_title="Percentual de Perdas (%)",
                hovermode='x unified',
                margin=dict(t=10, b=40, l=50, r=20),
                yaxis=dict(
                    range=[0, max(100, df_evolucao['perc_perdas'].max() * 1.3)],
                    tickformat='.1f'
                )
            )

            st.plotly_chart(fig_perdas, use_container_width=True)
        
        else:
            st.warning("⚠️ Dados insuficientes para análise temporal (mínimo 3 meses).")
    else:
        st.warning("⚠️ Período selecionado muito curto para análise temporal.")
else:
    st.warning("⚠️ Não há dados SIGIS disponíveis ou período insuficiente para análise temporal.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #665;'>Dashboard de Balanço Hídrico | CODEO/GEDES </div>", unsafe_allow_html=True)
