export interface ImageValidationResult {
  valid: boolean;
  error?: string;
}

export interface ImageConfig {
  maxCount: number;
  maxSizeMB: number;
  allowedTypes: string[];
}

const DEFAULT_CONFIG: ImageConfig = {
  maxCount: 5,
  maxSizeMB: 10,
  allowedTypes: ['jpg', 'jpeg', 'png', 'pdf'],
};

/**
 * 验证一组待上传的图片文件。
 * 返回第一个不满足要求的错误；全部通过则 valid=true。
 */
export function validateImageFiles(
  files: File[],
  config: Partial<ImageConfig> = {}
): ImageValidationResult {
  const cfg = { ...DEFAULT_CONFIG, ...config };

  if (files.length > cfg.maxCount) {
    return {
      valid: false,
      error: `最多上传 ${cfg.maxCount} 张图片，你选择了 ${files.length} 张`,
    };
  }

  const maxBytes = cfg.maxSizeMB * 1024 * 1024;

  for (const file of files) {
    const ext = file.name.split('.').pop()?.toLowerCase();

    if (!ext || !cfg.allowedTypes.includes(ext)) {
      return {
        valid: false,
        error: `不支持的文件类型：.${ext || '无'}，仅支持 JPG/PNG/PDF`,
      };
    }

    if (file.size > maxBytes) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      return {
        valid: false,
        error: `文件 "${file.name}" 过大（${sizeMB}MB），单个不超过 ${cfg.maxSizeMB}MB`,
      };
    }
  }

  return { valid: true };
}

/** 生成图片预览的临时 URL（调用方负责在不再需要时 revoke）。 */
export function getImagePreviewUrl(file: File): string {
  return URL.createObjectURL(file);
}

/** 判断文件是否为可预览图片（非 PDF）。 */
export function isPictureFile(file: File): boolean {
  const ext = file.name.split('.').pop()?.toLowerCase();
  return ext === 'jpg' || ext === 'jpeg' || ext === 'png';
}
