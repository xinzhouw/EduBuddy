<template>
  <div class="image-upload-area">
    <!-- Error message -->
    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
      closable
      @close="errorMessage = ''"
      class="mb-3"
    />

    <!-- Upload area (drag and click) -->
    <div
      class="upload-box"
      :class="{ dragging: isDragging }"
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @click="fileInput?.click()"
    >
      <input
        type="file"
        ref="fileInput"
        multiple
        accept=".jpg,.jpeg,.png,.pdf"
        @change="handleFileSelect"
        style="display: none"
      />
      <el-icon class="upload-icon"><UploadFilled /></el-icon>
      <p class="upload-text">{{ $t('homework.upload_click') }}</p>
      <p class="upload-hint">{{ $t('docs.file_types_hint') }}</p>
    </div>

    <!-- Image preview grid -->
    <div v-if="selectedFiles.length > 0" class="image-preview-grid mt-4">
      <div v-for="(file, index) in selectedFiles" :key="index" class="image-item">
        <div class="image-preview">
          <img
            v-if="isPictureFile(file)"
            :src="previewUrls[index]"
            :alt="file.name"
          />
          <div v-else class="pdf-placeholder">
            <el-icon><Document /></el-icon>
            <span>PDF</span>
          </div>
          <button class="delete-btn" @click.stop="removeImage(index)" :title="$t('common.delete')">
            ✕
          </button>
        </div>
        <p class="image-name" :title="file.name">{{ file.name }}</p>
        <p class="image-size">{{ formatFileSize(file.size) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue';
import { useI18n } from 'vue-i18n';
import { UploadFilled, Document } from '@element-plus/icons-vue';
import {
  validateImageFiles,
  getImagePreviewUrl,
  isPictureFile,
} from '@/utils/imageUpload';

const { t } = useI18n();

const props = withDefaults(
  defineProps<{
    maxCount?: number;
    maxSizeMB?: number;
  }>(),
  {
    maxCount: 5,
    maxSizeMB: 10,
  }
);

const emit = defineEmits<{
  'images-selected': [files: File[]];
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const isDragging = ref(false);
const errorMessage = ref('');
const selectedFiles = ref<File[]>([]);
const previewUrls = ref<string[]>([]);

// Rebuild preview URLs and release old ones whenever selected files change, to prevent memory leaks
watch(
  selectedFiles,
  (files) => {
    previewUrls.value.forEach((url) => URL.revokeObjectURL(url));
    previewUrls.value = files.map((f) =>
      isPictureFile(f) ? getImagePreviewUrl(f) : ''
    );
  },
  { deep: false }
);

onBeforeUnmount(() => {
  previewUrls.value.forEach((url) => url && URL.revokeObjectURL(url));
});

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = Array.from(target.files || []);
  processFiles(files);
  // Allow reselecting the same file
  target.value = '';
};

const handleDrop = (event: DragEvent) => {
  isDragging.value = false;
  const files = Array.from(event.dataTransfer?.files || []);
  processFiles(files);
};

const processFiles = (files: File[]) => {
  const imageFiles = files.filter((f) => {
    const ext = f.name.split('.').pop()?.toLowerCase();
    return ext === 'jpg' || ext === 'jpeg' || ext === 'png' || ext === 'pdf';
  });

  if (imageFiles.length === 0) {
    errorMessage.value = t('quiz.unsupported_file');
    return;
  }

  const validation = validateImageFiles(imageFiles, {
    maxCount: props.maxCount,
    maxSizeMB: props.maxSizeMB,
  });

  if (!validation.valid) {
    errorMessage.value = validation.error || t('common.failed');
    return;
  }

  errorMessage.value = '';
  selectedFiles.value = imageFiles;
  emit('images-selected', imageFiles);
};

const removeImage = (index: number) => {
  const next = selectedFiles.value.slice();
  next.splice(index, 1);
  selectedFiles.value = next;
  emit('images-selected', next);
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

/** Clear selected images, called by parent after successful send. */
const clear = () => {
  selectedFiles.value = [];
  emit('images-selected', []);
};

defineExpose({ clear });
</script>

<style scoped>
.image-upload-area {
  width: 100%;
}

.upload-box {
  border: 2px dashed #dcdfe4;
  border-radius: 8px;
  background: #f5f7fa;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.upload-box.dragging {
  border-color: #409eff;
  background: #ecf5ff;
}

.upload-box:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.upload-icon {
  font-size: 40px;
  color: #909399;
  margin-bottom: 8px;
}

.upload-text {
  font-size: 14px;
  color: #606266;
  margin: 6px 0;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

.image-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
  gap: 12px;
}

.image-item {
  position: relative;
}

.image-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border: 1px solid #dcdfe4;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-preview:hover .delete-btn {
  opacity: 1;
}

.pdf-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #909399;
  font-size: 12px;
}

.pdf-placeholder .el-icon {
  font-size: 30px;
}

.delete-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s;
}

.delete-btn:hover {
  background: #f56c6c;
}

.image-name {
  font-size: 12px;
  color: #606266;
  margin: 6px 0 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-size {
  font-size: 11px;
  color: #909399;
  margin: 0;
}
</style>
