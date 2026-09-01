# Arquitetura Geral — `article-loop`

O `article-loop` é um sistema multiagente projetado para o refinamento iterativo,
rigoroso e auditável de manuscritos científicos em formato LaTeX.

## 1. Visão Geral e Princípios Fundamentais

1. **Separação de Papéis e Contextos:** A topologia hierárquica divide a responsabilidade em 3 camadas:
   - **Gerente Geral (M00):** Coordenação global, agregação e acionamento.
   - **Subgerentes Departamentais (S10–S50):** 5 áreas do conhecimento científico (Estrutura, Matemática/Provas, Contribuição, Semântica/Linguagem, Formatação).
   - **Especialistas Operacionais (W11–W53):** 15 papéis pontuais e altamente especializados.
2. **Imutabilidade e Content-Addressing:** Artefatos intermediários, relatórios de portões, vereditos de jurados e diagnósticos são gravados uma única vez (*write-once*) e indexados via SHA-256.
3. **Avaliação Cega com Inversão:** Todo candidato (*challenger*) é comparado com o *champion* corrente em ordens neutras `[A, B]` e `[B, A]`, exigindo consistência de jurados para eliminar viés posicional.
4. **Hard Gates Científicos:** A correção matemática (`correctness_math_pass`) e provas de lemas são inegociáveis e intransponíveis.
