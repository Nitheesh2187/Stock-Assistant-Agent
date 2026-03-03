import { Newspaper } from 'lucide-react';
import NewsCard from './NewsCard';

function extractArticles(news) {
  if (!news) return [];
  if (Array.isArray(news)) return news;
  // Handle object wrappers: { feed: [...] }, { articles: [...] }, { news: [...] }, { results: [...] }
  for (const key of ['feed', 'articles', 'news', 'results', 'items']) {
    if (Array.isArray(news[key])) return news[key];
  }
  // Try first array-valued property
  for (const val of Object.values(news)) {
    if (Array.isArray(val)) return val;
  }
  return [];
}

export default function NewsSection({ news }) {
  const articles = extractArticles(news);

  if (articles.length === 0) return null;

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Newspaper className="h-4 w-4 text-surface-600 dark:text-surface-400" />
        <h3 className="text-sm font-semibold text-surface-900 dark:text-surface-100">Latest News</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {articles.slice(0, 6).map((article, i) => (
          <NewsCard key={article.url || article.link || i} article={article} />
        ))}
      </div>
    </div>
  );
}
