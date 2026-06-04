/**
 * 前端直接调用 Wikimedia Commons / Wikipedia API 搜索教育图片
 * 无需后端中转，浏览器直接请求（避免服务器网络封锁问题）
 */

export interface ImageSearchResult {
  url: string
  thumbnail: string
  title: string
  description: string
  source_url: string
}

// 简单内存缓存
const _cache = new Map<string, ImageSearchResult[]>()

/**
 * 从 Wikimedia Commons 搜索图片
 */
async function searchWikimediaCommons(keyword: string, limit: number): Promise<ImageSearchResult[]> {
  const params = new URLSearchParams({
    action: 'query',
    generator: 'search',
    gsrsearch: `filetype:bitmap|drawing ${keyword}`,
    gsrnamespace: '6',
    gsrlimit: String(limit + 3),
    prop: 'imageinfo',
    iiprop: 'url|extmetadata|size',
    iiurlwidth: '600',
    format: 'json',
    origin: '*',
  })

  try {
    const res = await fetch(`https://commons.wikimedia.org/w/api.php?${params}`, {
      signal: AbortSignal.timeout(8000),
    })
    if (!res.ok) return []
    const data = await res.json()
    const pages: Record<string, any> = data?.query?.pages || {}
    const results: ImageSearchResult[] = []

    for (const page of Object.values(pages)) {
      if (results.length >= limit) break
      const info = page.imageinfo?.[0]
      if (!info) continue
      const imgUrl: string = info.thumburl || info.url || ''
      if (!imgUrl) continue
      // 过滤非图片媒体文件
      if (/\.(ogg|webm|ogv|flac|mp3|wav|pdf)(\?|$)/i.test(imgUrl)) continue

      const rawDesc: string = info.extmetadata?.ImageDescription?.value || ''
      const desc = rawDesc.replace(/<[^>]+>/g, '').slice(0, 200)
      const title: string = (page.title || '').replace('File:', '')
      const sourceUrl = `https://commons.wikimedia.org/wiki/${encodeURIComponent(page.title || '')}`

      results.push({ url: imgUrl, thumbnail: imgUrl, title, description: desc, source_url: sourceUrl })
    }
    return results
  } catch {
    return []
  }
}

/**
 * 从 Wikipedia 页面获取主图
 */
async function searchWikipediaPageImage(keyword: string): Promise<ImageSearchResult[]> {
  try {
    // 先搜索页面
    const searchParams = new URLSearchParams({
      action: 'query',
      list: 'search',
      srsearch: keyword,
      srlimit: '1',
      format: 'json',
      origin: '*',
    })
    const searchRes = await fetch(`https://en.wikipedia.org/w/api.php?${searchParams}`, {
      signal: AbortSignal.timeout(8000),
    })
    if (!searchRes.ok) return []
    const searchData = await searchRes.json()
    const hits = searchData?.query?.search || []
    if (hits.length === 0) return []

    const pageTitle: string = hits[0].title

    // 获取页面主图
    const imgParams = new URLSearchParams({
      action: 'query',
      titles: pageTitle,
      prop: 'pageimages',
      pithumbsize: '600',
      format: 'json',
      origin: '*',
    })
    const imgRes = await fetch(`https://en.wikipedia.org/w/api.php?${imgParams}`, {
      signal: AbortSignal.timeout(8000),
    })
    if (!imgRes.ok) return []
    const imgData = await imgRes.json()
    const pages: Record<string, any> = imgData?.query?.pages || {}
    const results: ImageSearchResult[] = []

    for (const page of Object.values(pages)) {
      const thumb = page.thumbnail
      if (thumb?.source) {
        results.push({
          url: thumb.source,
          thumbnail: thumb.source,
          title: `${pageTitle} - Wikipedia`,
          description: `来自维基百科《${pageTitle}》页面的配图`,
          source_url: `https://en.wikipedia.org/wiki/${encodeURIComponent(pageTitle)}`,
        })
      }
    }
    return results
  } catch {
    return []
  }
}

/**
 * 综合搜索教育图片（主入口）
 * 同时从 Wikipedia 和 Wikimedia Commons 搜索，合并去重
 */
export async function searchEducationalImages(keyword: string, limit = 3): Promise<ImageSearchResult[]> {
  const cacheKey = `${keyword}:${limit}`
  if (_cache.has(cacheKey)) {
    return _cache.get(cacheKey)!
  }

  // 并发搜索两个来源
  const [wikiResults, commonsResults] = await Promise.allSettled([
    searchWikipediaPageImage(keyword),
    searchWikimediaCommons(keyword, limit),
  ])

  const wiki = wikiResults.status === 'fulfilled' ? wikiResults.value : []
  const commons = commonsResults.status === 'fulfilled' ? commonsResults.value : []

  // Wikipedia 主图优先，Commons 补充
  const all = [...wiki, ...commons]

  // 去重
  const seen = new Set<string>()
  const deduped: ImageSearchResult[] = []
  for (const r of all) {
    if (!seen.has(r.url)) {
      seen.add(r.url)
      deduped.push(r)
    }
  }

  const final = deduped.slice(0, limit)

  // 写缓存（最多 200 条）
  if (_cache.size >= 200) {
    const firstKey = _cache.keys().next().value
    if (firstKey) _cache.delete(firstKey)
  }
  _cache.set(cacheKey, final)

  return final
}
