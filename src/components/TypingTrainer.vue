<template>
  <div class="trainer-container">
    <header class="trainer-header">
      <h1>86五笔打字练习</h1>
      <div class="stats">
        <span>速度: <span class="stat-value">{{ wpm }}</span> WPM</span>
        <span>正确率: <span class="stat-value">{{ accuracy }}</span> %</span>
      </div>
    </header>

    <div class="file-controls">
      <div class="file-selector">
        <input
            type="file"
            ref="fileInput"
            @change="handleFileSelect"
            accept=".txt,.md,.text"
            style="display: none"
        />
        <button @click="selectFile" class="btn btn-primary">
          选择文本文件
        </button>
        <span v-if="selectedFileName" class="selected-file">
          已选择: {{ selectedFileName }}
        </span>
      </div>
<!--      <div class="text-controls">-->
<!--        <button @click="showTextarea = !showTextarea" class="btn btn-secondary">-->
<!--          {{ showTextarea ? '隐藏' : '显示' }}文本编辑-->
<!--        </button>-->
<!--        <button @click="resetText" class="btn btn-warning">-->
<!--          重置文本-->
<!--        </button>-->
<!--      </div>-->
    </div>

    <textarea
        v-if="showTextarea"
        class="source-input"
        v-model="sourceText"
        rows="6"
        placeholder="在这里粘贴或输入您想练习的文本...支持换行和段落格式"
    ></textarea>

    <div
        class="display-area"
        tabindex="0"
        @click="focusDisplay"
        @keydown="handleKeyDown"
        @scroll="handleScroll"
        ref="displayArea"
    >
      <div class="source-text-display">
        <!-- 前置占位符 -->
        <div
            v-if="visibleStart > 0"
            class="placeholder"
            :style="{ height: getPlaceholderHeight('before') + 'px' }"
        ></div>

        <!-- 可见字符 -->
        <span
            v-for="(char, index) in visibleChars"
            :key="visibleStart + index"
            :class="getCharClass(visibleStart + index)"
        >{{ char }}</span>

        <!-- 后置占位符 -->
        <div
            v-if="visibleEnd < sourceChars.length"
            class="placeholder"
            :style="{ height: getPlaceholderHeight('after') + 'px' }"
        ></div>
      </div>
    </div>

    <div class="hint-box">
      <span>当前提示: </span>
      <span class="wubi-code">{{ wubiHint }}</span>
      <span> ({{ currentChar }})</span>
    </div>

    <!-- 添加调试信息（可选，用于测试） -->
<!--    <div class="debug-info" style="font-size: 12px; color: #666; margin-top: 10px;">-->
<!--      <div>当前输入: "{{ userInput }}"</div>-->
<!--      <div>输入长度: {{ userInput.length }}</div>-->
<!--      <div>历史记录长度: {{ typingHistory.length }}</div>-->
<!--      <div>当前索引: {{ currentIndex }}</div>-->
<!--    </div>-->

    <!-- 修改隐藏输入框 -->
    <input
        type="text"
        class="hidden-input"
        ref="hiddenInput"
        v-model="hiddenInputValue"
        @input="handleHiddenInput"
        @keydown="handleHiddenKeyDown"
        @compositionstart="handleCompositionStart"
        @compositionend="handleCompositionEnd"
        @blur="focusDisplay"
    />
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "TypingTrainer",
  data() {
    return {
      sourceText: "我是一个java程序员，我现在的输入法使用的86版的五笔。",
      userInput: "",
      hiddenInputValue: "",
      isComposing: false,
      wubiDict: {},
      wubiHint: "请开始",
      startTime: 0,
      correctChars: 0,
      totalTypedChars: 0,
      selectedFileName: "",
      showTextarea: false,
      defaultText: "我是一个java程序员，我现在的输入法使用的86版的五笔。",
      // 新增：用于回退功能的历史记录
      typingHistory: [], // 记录每次输入的字符和是否正确
      renderChunkSize: 500,
      visibleStart: 0,
      visibleEnd: 500,
    };
  },
  computed: {
    sourceChars() {
      return this.sourceText.split("");
    },
    visibleChars() {
      const chars = this.sourceChars;
      const start = Math.max(0, this.visibleStart);
      const end = Math.min(chars.length, this.visibleEnd);
      return chars.slice(start, end);
    },
    currentIndex() {
      return this.userInput.length;
    },
    currentChar() {
      if (this.currentIndex < this.sourceText.length) {
        return this.sourceText[this.currentIndex];
      }
      return "";
    },
    wpm() {
      if (!this.startTime || this.totalTypedChars === 0) {
        return 0;
      }
      const elapsedTimeInMinutes = (Date.now() - this.startTime) / 1000 / 60;
      const words = this.totalTypedChars;
      return Math.round(words / elapsedTimeInMinutes);
    },
    accuracy() {
      if (this.totalTypedChars === 0) {
        return 100;
      }
      return ((this.correctChars / this.totalTypedChars) * 100).toFixed(1);
    },
  },
  methods: {
    async fetchWubiDict() {
      try {
        const response = await axios.get("/wubi86.json");
        this.wubiDict = response.data;
        console.log("加载五笔码表成功:", response.data);
        this.updateHint();
      } catch (error) {
        console.error("加载五笔码表失败:", error);
        this.wubiHint = "码表加载失败！";
      }
    },
    // 增强焦点管理
    focusDisplay() {
      this.$nextTick(() => {
        // 检查是否正在选择文本
        const selection = window.getSelection();
        if (
          selection &&
          selection.type === "Range" &&
          selection.anchorNode &&
          this.$refs.displayArea &&
          this.$refs.displayArea.contains(selection.anchorNode)
        ) {
          // 用户正在选择 displayArea 的文本，不强制聚焦隐藏输入框
          return;
        }
        // 只聚焦隐藏输入框，让它处理所有输入
        if (this.$refs.hiddenInput) {
          this.$refs.hiddenInput.focus();
        }
      });
    },
    handleKeyDown(event) {
      if (event.key === 'Backspace') {
        event.preventDefault();
        event.stopPropagation();
        this.handleBackspace();
      } else if (event.key === 'Enter') {
        event.preventDefault();
        this.handleEnter();
      } else if (event.key === 'Tab') {
        event.preventDefault();
      }

      // 对于可打印字符，阻止在 displayArea 上的处理，让隐藏输入框处理
      if (event.key.length === 1 && !this.isComposing) {
        event.preventDefault();
        event.stopPropagation();
        // 不在这里处理字符输入，交给隐藏输入框
        return;
      }
    },
    handleKeyPress(event) {
      // 完全阻止 keypress 事件，避免重复处理
      event.preventDefault();
      event.stopPropagation();
    },
    handleHiddenInput() {
      // 只在未组合输入时处理
      if (this.isComposing) return;

      const currentValue = this.hiddenInputValue;
      if (currentValue) {
        for (const char of currentValue) {
          this.processCharacterInput(char);
        }
        this.$nextTick(() => {
          this.hiddenInputValue = "";
        });
      }
    },
    handleCompositionStart() {
      console.log('composition start');
      this.isComposing = true;
    },
    handleCompositionEnd() {
      // 只结束组合，不处理输入
      this.isComposing = false;
    },
    processCharacterInput(char) {
      // 只在未完成时处理
      if (this.currentIndex >= this.sourceText.length) return;

      // 记录输入历史
      const isCorrect = char === this.sourceText[this.currentIndex];
      this.typingHistory.push({ char, isCorrect });

      // 更新输入内容
      this.userInput += char;
      this.totalTypedChars += 1;
      if (isCorrect) this.correctChars += 1;

      // 如果是第一次输入，记录开始时间
      if (this.userInput.length === 1) {
        this.startTime = Date.now();
      }

      // 更新提示和光标
      this.updateHint();
    },
    handleBackspace() {
      console.log('handleBackspace called, userInput length:', this.userInput.length); // 调试日志

      if (this.userInput.length > 0) {
        // 获取最后一个输入的历史记录
        const lastEntry = this.typingHistory.pop();
        console.log('last entry:', lastEntry); // 调试日志

        if (lastEntry) {
          // 回退用户输入
          this.userInput = this.userInput.slice(0, -1);

          // 回退统计数据
          this.totalTypedChars = Math.max(0, this.totalTypedChars - 1);

          if (lastEntry.isCorrect) {
            this.correctChars = Math.max(0, this.correctChars - 1);
          }

          // 如果回退到开始位置，重置开始时间
          if (this.userInput.length === 0) {
            this.startTime = 0;
          }
        }

        this.updateHint();

        // 强制更新视图
        this.$forceUpdate();

        // 保持焦点
        this.$nextTick(() => {
          this.$refs.hiddenInput.focus();
          this.$refs.displayArea.focus();
        });
      }
    },
    handleEnter() {
      if (this.currentChar === '\n') {
        this.processCharacterInput('\n');
      }
    },
    selectFile() {
      this.$refs.fileInput.click();
    },
    handleFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        const fileSizeKB = file.size / 1024;
        const maxSizeKB = 500;

        if (fileSizeKB > maxSizeKB) {
          const proceed = confirm(
              `文件大小为 ${Math.round(fileSizeKB)}KB，较大的文件可能会影响性能。\n` +
              `建议使用小于 ${maxSizeKB}KB 的文件。\n\n` +
              `是否继续加载？`
          );
          if (!proceed) {
            event.target.value = "";
            return;
          }
        }

        this.selectedFileName = file.name;
        const reader = new FileReader();
        reader.onload = (e) => {
          const content = e.target.result.trim();

          if (content.length > 10000) {
            const proceed = confirm(
                `文本长度为 ${content.length} 字符，较长的文本可能会影响性能。\n` +
                `是否只加载前 10000 字符？\n\n` +
                `点击"确定"加载前10000字符，点击"取消"加载全部内容。`
            );
            this.sourceText = proceed ? content.substring(0, 10000) : content;
          } else {
            this.sourceText = content;
          }
        };
        reader.onerror = () => {
          alert('文件读取失败，请重新选择文件');
          this.selectedFileName = "";
        };
        reader.readAsText(file, 'UTF-8');
      }
    },
    resetText() {
      this.sourceText = this.defaultText;
      this.selectedFileName = "";
      this.$refs.fileInput.value = "";
    },
    // 重置所有状态的方法
    resetAllState() {
      this.userInput = "";
      this.startTime = 0;
      this.correctChars = 0;
      this.totalTypedChars = 0;
      this.typingHistory = []; // 清空历史记录
      this.visibleStart = 0;
      this.visibleEnd = Math.min(this.renderChunkSize, this.sourceText.length);
    },
    updateHint() {
      if (this.currentIndex < this.sourceText.length) {
        const charToType = this.sourceText[this.currentIndex];
        this.wubiHint =
            this.wubiDict[charToType] || `「${charToType}」无编码`;
      } else {
        this.wubiHint = "已完成！";
        this.startTime = 0;
      }
      this.updateVisibleRange();
      this.$nextTick(() => {
        this.scrollToCurrentPosition();
      });
    },
    updateVisibleRange() {
      const currentPos = this.currentIndex;
      const chunkSize = this.renderChunkSize;
      const halfChunk = Math.floor(chunkSize / 2);

      if (currentPos < this.visibleStart + 50 || currentPos >= this.visibleEnd - 50) {
        this.visibleStart = Math.max(0, currentPos - halfChunk);
        this.visibleEnd = Math.min(this.sourceChars.length, this.visibleStart + chunkSize);

        if (this.visibleEnd === this.sourceChars.length) {
          this.visibleStart = Math.max(0, this.visibleEnd - chunkSize);
        }

        if (this.visibleStart === 0) {
          this.visibleEnd = Math.min(this.sourceChars.length, chunkSize);
        }
      }
    },
    handleScroll(event) {
      clearTimeout(this.scrollTimer);
      this.scrollTimer = setTimeout(() => {
        this.updateVisibleRangeByScroll(event.target);
      }, 16);
    },
    updateVisibleRangeByScroll(element) {
      const scrollTop = element.scrollTop;
      const clientHeight = element.clientHeight;
      const lineHeight = 43.2;

      const visibleLines = Math.ceil(clientHeight / lineHeight);
      const firstVisibleLine = Math.floor(scrollTop / lineHeight);

      const avgCharsPerLine = 30;
      const bufferLines = 5;

      const newStart = Math.max(0, (firstVisibleLine - bufferLines) * avgCharsPerLine);
      const newEnd = Math.min(
          this.sourceChars.length,
          (firstVisibleLine + visibleLines + bufferLines) * avgCharsPerLine
      );

      if (Math.abs(newStart - this.visibleStart) > 50 || Math.abs(newEnd - this.visibleEnd) > 50) {
        this.visibleStart = newStart;
        this.visibleEnd = newEnd;
      }
    },
    getPlaceholderHeight(type) {
      const lineHeight = 43.2;
      const avgCharsPerLine = 30;

      if (type === 'before') {
        const lines = Math.ceil(this.visibleStart / avgCharsPerLine);
        return lines * lineHeight;
      } else {
        const remainingChars = this.sourceChars.length - this.visibleEnd;
        const lines = Math.ceil(remainingChars / avgCharsPerLine);
        return lines * lineHeight;
      }
    },
    scrollToCurrentPosition() {
      this.$nextTick(() => {
        const displayArea = this.$refs.displayArea.querySelector('.source-text-display');
        const currentSpan = this.$el.querySelector('.char-current');

        if (displayArea && currentSpan) {
          currentSpan.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
          });
        } else if (displayArea) {
          this.manualScrollToPosition(displayArea);
        }
      });
    },
    manualScrollToPosition(displayArea) {
      const currentPos = this.currentIndex;
      const lineHeight = 43.2;
      const avgCharsPerLine = 30;
      const currentLine = Math.floor(currentPos / avgCharsPerLine);
      const targetScrollTop = currentLine * lineHeight;

      const containerHeight = displayArea.clientHeight;
      const centeredScrollTop = Math.max(0, targetScrollTop - containerHeight / 2);

      displayArea.scrollTo({
        top: centeredScrollTop,
        behavior: 'smooth'
      });
    },
    getCharClass(index) {
      if (index < this.currentIndex) {
        return this.userInput[index] === this.sourceText[index]
            ? "char-correct"
            : "char-wrong";
      }
      if (index === this.currentIndex) {
        return "char-current";
      }
      return "char-pending";
    },
    handleHiddenKeyDown(event) {
      console.log('keydown:', event.key, 'isComposing:', this.isComposing);

      // 如果正在组合输入，不处理退格键，交给输入法
      if (this.isComposing) {
        return;
      }

      // 处理退格键
      if (event.key === 'Backspace') {
        event.preventDefault();
        this.handleBackspace();
        return;
      }

      // 处理回车键
      if (event.key === 'Enter') {
        event.preventDefault();
        this.handleEnter();
        return;
      }

      // 只处理明确的非输入法字符（如标点符号、数字等）
      // 英文字母交给组合事件处理，避免输入法冲突
      if (event.key.length === 1 && !event.key.match(/^[a-zA-Z]$/)) {
        event.preventDefault();
        this.processCharacterInput(event.key);
      }
    },
  },
  mounted() {
    this.fetchWubiDict();
    this.focusDisplay();
    document.addEventListener("click", this.focusDisplay);

    this.$nextTick(() => {
      this.scrollToCurrentPosition();
    });
  },
  beforeDestroy() {
    document.removeEventListener("click", this.focusDisplay);
  },
  watch: {
    sourceText() {
      this.resetAllState(); // 使用新的重置方法
      this.updateHint();

      this.$nextTick(() => {
        const displayArea = this.$refs.displayArea;
        if (displayArea) {
          displayArea.scrollTop = 0;
        }
      });
    },
    currentIndex() {
      this.$nextTick(() => {
        this.scrollToCurrentPosition();
      });
    },
  },
};
</script>

<style scoped>
.trainer-container {
  max-width: 800px;
  margin: 20px auto;
  padding: 20px 30px;
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC",
  "Microsoft YaHei", sans-serif;
  background-color: #f7f7f7;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.trainer-header {
  text-align: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 15px;
}
.trainer-header h1 {
  margin: 0;
  color: #333;
}
.stats {
  margin-top: 10px;
  color: #666;
  font-size: 16px;
}
.stats span {
  margin: 0 15px;
}
.stat-value {
  color: #007bff;
  font-weight: bold;
}

.file-controls {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.file-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.text-controls {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s ease;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

.btn-warning {
  background-color: #ffc107;
  color: #212529;
}

.btn-warning:hover {
  background-color: #e0a800;
}

.selected-file {
  color: #28a745;
  font-size: 14px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .file-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .file-selector,
  .text-controls {
    justify-content: center;
  }
}

.source-input {
  width: 100%;
  box-sizing: border-box;
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 16px;
  min-height: 120px;
  max-height: 300px;
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;
}

.display-area {
  background-color: #fff;
  border-radius: 8px;
  border: 2px solid #007bff;
  cursor: text;
  margin-bottom: 20px;
  outline: none;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  user-select: text;
  overflow-y: auto;
  min-height: 320px;
  max-height: 400px;
}

.source-text-display {
  padding: 20px;
  font-size: 24px;
  line-height: 1.8;
  letter-spacing: 1px;
  text-align: left;
  white-space: pre-wrap;
  word-wrap: break-word;
  user-select: text;
  min-height: 320px;
  max-height: 800px;
}

.source-text-display::-webkit-scrollbar {
  width: 8px;
}

.source-text-display::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.source-text-display::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.source-text-display::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.placeholder {
  width: 100%;
  /* pointer-events: none; 移除以允许跨行选择 */
}

.char-correct {
  color: #28a745;
}
.char-wrong {
  color: #dc3545;
  text-decoration: underline;
}
.char-pending {
  color: #6c757d;
}
.char-current {
  background-color: #007bff;
  color: #fff;
  border-radius: 3px;
  padding: 2px 4px;
  margin: 0 1px;
  box-shadow: 0 0 8px rgba(0, 123, 255, 0.5);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.hint-box {
  text-align: center;
  font-size: 20px;
  padding: 15px;
  background-color: #e9ecef;
  border-radius: 6px;
}
.wubi-code {
  font-family: "Courier New", Courier, monospace;
  font-size: 24px;
  color: #c41a16;
  font-weight: bold;
  margin: 0 5px;
}

/* 隐藏输入框，但保持其功能用于输入法支持 */
.hidden-input {
  position: absolute;
  left: -9999px;
  opacity: 0;
  pointer-events: none;
}
</style>
