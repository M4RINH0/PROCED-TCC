// Inicialização do Mermaid integrada ao tema do PROCED no MkDocs Material
document$.subscribe(() => {
  if (typeof mermaid === "undefined") return;

  const isDark = document.body.getAttribute("data-md-color-scheme") === "slate";

  mermaid.initialize({
    startOnLoad: false,
    theme: isDark ? "dark" : "base",
    themeVariables: {
      darkMode: isDark,
      background: "transparent",
      fontFamily: "Archivo, sans-serif",
      fontSize: "13px",

      // Nós do grafo
      nodeBorder: isDark ? "#46B8A4" : "#0E6B5C",
      nodeTextColor: isDark ? "#E6EDEA" : "#13201C",

      // Subgrafos / Clusters
      clusterBorder: isDark ? "#26322E" : "#D2DAD7",
      titleColor: isDark ? "#46B8A4" : "#0E6B5C",

      // Linhas e conexões
      edgeColor: isDark ? "#98A5A0" : "#56635E",
      lineColor: isDark ? "#98A5A0" : "#56635E",

      // Diagramas de Sequência
      actorBorder: isDark ? "#46B8A4" : "#0E6B5C",
      actorTextColor: isDark ? "#E6EDEA" : "#13201C",
      actorLineColor: isDark ? "#26322E" : "#D2DAD7",
      signalColor: isDark ? "#46B8A4" : "#0E6B5C",
      signalTextColor: isDark ? "#E6EDEA" : "#13201C",
      labelBoxBorderColor: isDark ? "#46B8A4" : "#0E6B5C",
      labelTextColor: isDark ? "#E6EDEA" : "#13201C",
      noteBkgColor: isDark ? "#2A2310" : "#FBEBC4",
      noteBorderColor: "#F2B01E",
      noteTextColor: isDark ? "#E6EDEA" : "#13201C",

      // Diagramas de Entidade-Relacionamento
      attributeBackgroundColorOdd: isDark ? "#18211E" : "#FAFCFB",
      attributeBackgroundColorEven: isDark ? "#141C19" : "#F5F7F6"
    }
  });

  // Executa o render em todos os blocos .mermaid
  mermaid.run({
    querySelector: ".mermaid"
  });
});
