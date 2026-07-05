# Currículos Lattes — PGEDU/UFBA

Análise dos currículos Lattes dos **docentes permanentes** do Programa de Pós-Graduação em Educação (PGEDU) da Universidade Federal da Bahia (UFBA).

## 📊 Visão Geral

- **49 docentes permanentes**
- Currículos baixados via scriptLattes (Selenium + 2Captcha)
- Dados consolidados: produção bibliográfica, projetos, orientações, bancas, formação, áreas
- Google Scholar integrado (citações, h-index)
- Página HTML interativa com gráficos, rankings e busca

## 🔗 Links

- **Página:** [leofn.com/lattes_pgedu](https://leofn.com/lattes_pgedu)
- **Repositório:** [github.com/leofn/lattes_pgedu](https://github.com/leofn/lattes_pgedu)
- **Fonte:** [pgedu.faced.ufba.br/pt-br/corpo-docente](https://pgedu.faced.ufba.br/pt-br/corpo-docente)

## 📁 Estrutura

```
data/raw/           — JSONs originais dos currículos
data/processed/     — Dataset consolidado + dados temporais
docs/index.html     — Página HTML interativa
```

## 🛠️ Metodologia

1. Scraping da página do corpo docente (UFBA Plone)
2. Download dos currículos via scriptLattes (Selenium + 2Captcha)
3. Consolidação e extração de métricas
4. Busca de perfis no Google Scholar
5. Geração de página HTML com Chart.js

## 📜 Licença

Dados públicos dos currículos Lattes (CNpq). Análise por LABHD-UFBA.