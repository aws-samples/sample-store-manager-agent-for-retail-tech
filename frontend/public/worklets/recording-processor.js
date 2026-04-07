/**
 * AudioWorklet Processor for Transcribe Streaming
 * 
 * マイク入力をPCM形式に変換してメインスレッドに送信
 * 参考: https://aws.amazon.com/blogs/machine-learning/stream-multi-channel-audio-to-amazon-transcribe-using-the-web-audio-api/
 */

class RecordingProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    
    // 設定
    const processorOptions = options.processorOptions || {};
    this.bufferSize = processorOptions.bufferSize || 4096;
    
    // バッファ
    this._buffer = new Float32Array(this.bufferSize);
    this._bufferIndex = 0;
    this._isRecording = true;
    
    // メッセージハンドラ
    this.port.onmessage = (event) => {
      if (event.data.command === 'stop') {
        this._isRecording = false;
        // 残りのバッファを送信
        if (this._bufferIndex > 0) {
          this._sendBuffer();
        }
        this.port.postMessage({ message: 'STOPPED' });
      }
    };
  }

  /**
   * バッファをPCMエンコードして送信
   */
  _sendBuffer() {
    const pcmData = this._pcmEncode(this._buffer.slice(0, this._bufferIndex));
    this.port.postMessage({
      message: 'AUDIO_DATA',
      audioData: pcmData,
    });
    this._bufferIndex = 0;
  }

  /**
   * Float32Array を PCM Int16 に変換
   * @param {Float32Array} input - 入力データ (-1.0 ~ 1.0)
   * @returns {Uint8Array} - PCM エンコードされたデータ
   */
  _pcmEncode(input) {
    const buffer = new ArrayBuffer(input.length * 2);
    const view = new DataView(buffer);
    
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]));
      // 16bit PCM: -32768 ~ 32767
      view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    
    return new Uint8Array(buffer);
  }

  /**
   * 音声処理（AudioWorkletProcessor必須メソッド）
   */
  process(inputs, outputs, parameters) {
    if (!this._isRecording) {
      return false;
    }

    const input = inputs[0];
    if (!input || input.length === 0) {
      return true;
    }

    const channelData = input[0];
    if (!channelData) {
      return true;
    }

    // バッファに追加
    for (let i = 0; i < channelData.length; i++) {
      this._buffer[this._bufferIndex++] = channelData[i];
      
      // バッファが満杯になったら送信
      if (this._bufferIndex >= this.bufferSize) {
        this._sendBuffer();
      }
    }

    return true;
  }
}

registerProcessor('recording-processor', RecordingProcessor);
