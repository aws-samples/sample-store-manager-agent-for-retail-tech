/**
 * useVoiceInput - 音声入力カスタムフック
 * 
 * Amazon Transcribe Streamingを使用したリアルタイム音声認識
 * AudioWorklet使用（ベストプラクティス）
 * 
 * 参考: https://aws.amazon.com/blogs/machine-learning/stream-multi-channel-audio-to-amazon-transcribe-using-the-web-audio-api/
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';
import {
  TranscribeStreamingClient,
  StartStreamTranscriptionCommand,
  LanguageCode,
  MediaEncoding,
} from '@aws-sdk/client-transcribe-streaming';

export type RecordingState = 'idle' | 'recording' | 'processing' | 'error';

export interface UseVoiceInputOptions {
  language?: string;
  sampleRate?: number;
  onInterimResult?: (text: string) => void;
  onFinalResult?: (text: string) => void;
  onError?: (error: Error) => void;
}

export interface UseVoiceInputReturn {
  state: RecordingState;
  isRecording: boolean;
  duration: number;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<string>;
  cancelRecording: () => void;
}

const SAMPLE_RATE = 16000;
const BUFFER_SIZE = 4096;

export function useVoiceInput(options: UseVoiceInputOptions = {}): UseVoiceInputReturn {
  const { 
    language = 'ja-JP', 
    sampleRate = SAMPLE_RATE,
    onInterimResult, 
    onFinalResult, 
    onError 
  } = options;

  const [state, setState] = useState<RecordingState>('idle');
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Refs
  const clientRef = useRef<TranscribeStreamingClient | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const durationIntervalRef = useRef<number | null>(null);
  const finalTextRef = useRef<string>('');
  const audioChunksRef = useRef<Uint8Array[]>([]);
  const streamEndedRef = useRef<boolean>(false);
  const resolveAudioStreamRef = useRef<(() => void) | null>(null);

  // クリーンアップ
  useEffect(() => {
    return () => {
      cleanup();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cleanup = useCallback(() => {
    // タイマー停止
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }
    
    // AudioWorkletに停止を通知
    if (workletNodeRef.current) {
      workletNodeRef.current.port.postMessage({ command: 'stop' });
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }
    
    // マイクストリーム停止
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop());
      audioStreamRef.current = null;
    }
    
    // AudioContext終了
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    clientRef.current = null;
    streamEndedRef.current = true;
    
    if (resolveAudioStreamRef.current) {
      resolveAudioStreamRef.current();
      resolveAudioStreamRef.current = null;
    }
  }, []);


  // AWS認証情報を取得してTranscribeクライアントを初期化
  const initializeClient = useCallback(async () => {
    const session = await fetchAuthSession();
    const credentials = session.credentials;

    if (!credentials) {
      throw new Error('AWS認証情報を取得できませんでした');
    }

    clientRef.current = new TranscribeStreamingClient({
      region: import.meta.env.VITE_APP_REGION || 'ap-northeast-1',
      credentials: {
        accessKeyId: credentials.accessKeyId,
        secretAccessKey: credentials.secretAccessKey,
        sessionToken: credentials.sessionToken,
      },
    });
  }, []);

  // 音声ストリームジェネレーター（AWS SDK形式）
  async function* createAudioStream() {
    while (!streamEndedRef.current) {
      if (audioChunksRef.current.length > 0) {
        const chunk = audioChunksRef.current.shift()!;
        yield { AudioEvent: { AudioChunk: chunk } };
      } else {
        await new Promise<void>((resolve) => {
          resolveAudioStreamRef.current = resolve;
        });
      }
    }
  }

  // Transcribe Streamingを開始
  const startTranscription = useCallback(async () => {
    if (!clientRef.current) return;

    try {
      const command = new StartStreamTranscriptionCommand({
        LanguageCode: language as LanguageCode,
        MediaEncoding: MediaEncoding.PCM,
        MediaSampleRateHertz: sampleRate,
        AudioStream: createAudioStream(),
      });

      const response = await clientRef.current.send(command);

      if (response.TranscriptResultStream) {
        for await (const event of response.TranscriptResultStream) {
          if (event.TranscriptEvent?.Transcript?.Results) {
            for (const result of event.TranscriptEvent.Transcript.Results) {
              if (result.Alternatives && result.Alternatives.length > 0) {
                const transcript = result.Alternatives[0].Transcript || '';

                if (result.IsPartial) {
                  // 中間結果：確定テキスト + 現在の中間テキストを表示
                  const displayText = finalTextRef.current 
                    ? `${finalTextRef.current}${transcript}` 
                    : transcript;
                  onInterimResult?.(displayText);
                } else {
                  // 確定結果：累積して通知
                  finalTextRef.current += transcript;
                  onFinalResult?.(finalTextRef.current);
                }
              }
            }
          }
        }
      }
    } catch (err) {
      console.error('Transcribe error:', err);
      if (state === 'recording') {
        setError('音声認識でエラーが発生しました');
        setState('error');
        onError?.(err instanceof Error ? err : new Error(String(err)));
      }
    }
  }, [language, sampleRate, onInterimResult, onFinalResult, onError, state]);


  // 録音開始
  const startRecording = useCallback(async () => {
    if (state === 'recording') return;

    try {
      setError(null);
      finalTextRef.current = '';
      audioChunksRef.current = [];
      streamEndedRef.current = false;

      // AWS認証情報を取得
      await initializeClient();

      // マイクアクセスを取得
      audioStreamRef.current = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: sampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // AudioContextを作成
      audioContextRef.current = new AudioContext({ sampleRate: sampleRate });
      
      // AudioWorkletモジュールを読み込み
      await audioContextRef.current.audioWorklet.addModule('/worklets/recording-processor.js');
      
      // AudioWorkletNodeを作成
      workletNodeRef.current = new AudioWorkletNode(
        audioContextRef.current, 
        'recording-processor',
        {
          processorOptions: {
            bufferSize: BUFFER_SIZE,
            sampleRate: sampleRate,
          },
        }
      );

      // AudioWorkletからのメッセージを処理
      workletNodeRef.current.port.onmessage = (event) => {
        if (event.data.message === 'AUDIO_DATA') {
          audioChunksRef.current.push(event.data.audioData);
          
          // 待機中のPromiseを解決
          if (resolveAudioStreamRef.current) {
            resolveAudioStreamRef.current();
            resolveAudioStreamRef.current = null;
          }
        }
      };

      // マイク入力をAudioWorkletに接続
      const source = audioContextRef.current.createMediaStreamSource(audioStreamRef.current);
      source.connect(workletNodeRef.current);
      // 出力は不要（録音のみ）だが、接続しないとprocessが呼ばれない場合がある
      workletNodeRef.current.connect(audioContextRef.current.destination);

      // 状態更新
      setState('recording');
      startTimeRef.current = Date.now();

      // 録音時間の更新
      durationIntervalRef.current = window.setInterval(() => {
        if (startTimeRef.current) {
          setDuration(Date.now() - startTimeRef.current);
        }
      }, 100);

      // Transcribe Streamingを開始
      startTranscription();

    } catch (err) {
      console.error('Recording start error:', err);
      cleanup();
      
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      if (errorMessage.includes('Permission denied') || errorMessage.includes('NotAllowedError')) {
        setError('マイクへのアクセスが拒否されました');
      } else if (errorMessage.includes('addModule')) {
        setError('AudioWorkletの読み込みに失敗しました');
      } else {
        setError('録音の開始に失敗しました');
      }
      setState('error');
      onError?.(err instanceof Error ? err : new Error(String(err)));
    }
  }, [state, sampleRate, initializeClient, startTranscription, cleanup, onError]);


  // 録音停止
  const stopRecording = useCallback(async (): Promise<string> => {
    if (state !== 'recording') return '';

    setState('processing');
    streamEndedRef.current = true;

    // 待機中のPromiseを解決
    if (resolveAudioStreamRef.current) {
      resolveAudioStreamRef.current();
      resolveAudioStreamRef.current = null;
    }

    cleanup();

    setState('idle');
    setDuration(0);
    startTimeRef.current = null;

    return finalTextRef.current.trim();
  }, [state, cleanup]);

  // 録音キャンセル
  const cancelRecording = useCallback(() => {
    streamEndedRef.current = true;
    cleanup();
    setState('idle');
    setDuration(0);
    setError(null);
    finalTextRef.current = '';
    startTimeRef.current = null;
  }, [cleanup]);

  return {
    state,
    isRecording: state === 'recording',
    duration,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
