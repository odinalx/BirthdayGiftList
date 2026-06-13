# NextJS Boilerplate

Ce projet est une **boilerplate/template** de projet Next.js pré-configurée avec les technologies modernes suivantes :

## 🛠️ Technologies incluses

- **Next.js 14** - Framework React avec App Router
- **TypeScript** - Typage statique pour JavaScript
- **Tailwind CSS** - Framework CSS utilitaire
- **shadcn/ui** - Composants UI réutilisables et personnalisables
- **ESLint + Prettier** - Linting et formatage automatique
- **Formatage automatique** - Configuration pour formater le code à la sauvegarde

## 🎯 Objectif

Cette boilerplate sert de **base de départ** pour créer de nouveaux projets. Elle n'est **pas destinée à être modifiée pour être lancée** en tant que projet final, mais plutôt à être copiée/clonée comme point de départ pour d'autres projets.

## 🚀 Utilisation

### Pour utiliser cette boilerplate :

1. **Cloner ce repository** dans un nouveau dossier de projet
2. **Supprimer le `.git`** existant et initialiser un nouveau repository
3. **Modifier les informations** du projet (nom, description, etc.)
4. **Installer les dépendances** et commencer le développement

### Commandes classiques :

```bash
# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev

# Build pour la production
npm run build

# Lancer en production
npm start

# Linter
npm run lint

# Formater le code
npm run format
```

## 📁 Structure du projet

```
├── app/                 # App Router (Next.js 14)
├── components/          # Composants réutilisables
├── lib/                 # Utilitaires et configurations
├── public/              # Assets statiques
└── styles/              # Styles globaux
```

## ⚙️ Configuration

- **TypeScript** configuré avec des règles strictes
- **Tailwind CSS** avec configuration personnalisée
- **shadcn/ui** avec thème sombre/clair
- **ESLint** avec règles Next.js et TypeScript
- **Prettier** pour le formatage automatique
- **Formatage à la sauvegarde** configuré dans VS Code

## 🔧 Personnalisation

Après avoir cloné cette boilerplate :

1. Modifiez le `package.json` avec les informations de votre projet
2. Ajustez la configuration Tailwind dans `tailwind.config.js`
3. Personnalisez les composants shadcn/ui selon vos besoins
4. Modifiez les couleurs et thèmes dans `globals.css`

---

**Note :** Cette boilerplate est conçue pour être un point de départ solide et moderne pour vos projets Next.js. Elle inclut les meilleures pratiques et outils actuels pour un développement efficace.
