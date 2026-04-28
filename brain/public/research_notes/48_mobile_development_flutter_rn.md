# Research Note 48 — Mobile Development: Flutter & React Native

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal**: 2026-04-17
**Sumber**: Pengetahuan teknis + roadmap.sh best practices
**Relevance SIDIX**: SIDIX sebagai LLM platform dapat diperluas ke mobile agar pengguna bisa mengakses brain_qa dari smartphone. Flutter atau React Native adalah pilihan utama untuk membangun SIDIX Mobile Client yang dapat melakukan query ke API SIDIX, menyimpan history offline, dan mendukung notifikasi push ketika knowledge base diperbarui.
**Tags**: `flutter`, `dart`, `react-native`, `mobile`, `state-management`, `expo`, `fastlane`, `deep-links`, `push-notifications`

---

## 1. Flutter — Overview & Dart Basics

Flutter adalah UI toolkit dari Google untuk membangun app natively compiled dari satu codebase ke mobile, web, dan desktop. Flutter menggunakan Dart sebagai bahasa pemrograman.

### Dart Language Basics
```dart
// Tipe data dan null safety
String name = 'SIDIX';
int count = 42;
double score = 0.95;
bool isActive = true;
List<String> tags = ['rag', 'bm25', 'llm'];
Map<String, dynamic> metadata = {'version': '1.0', 'lang': 'id'};

// Null safety
String? maybeNull = null;       // nullable
String nonNull = 'guaranteed';  // non-nullable

// Null-aware operators
String display = maybeNull ?? 'default';  // null coalescing
int? length = maybeNull?.length;          // null-safe member access

// Functions
String formatMessage({required String text, String prefix = 'SIDIX'}) {
  return '$prefix: $text';
}

// Arrow function
int double(int n) => n * 2;

// Async/await
Future<List<Message>> fetchMessages(String sessionId) async {
  final response = await http.get(Uri.parse('/api/sessions/$sessionId/messages'));
  final json = jsonDecode(response.body) as List;
  return json.map((j) => Message.fromJson(j)).toList();
}

// Stream
Stream<String> streamResponse(String query) async* {
  final request = http.Request('POST', Uri.parse('/api/ask'));
  request.body = jsonEncode({'q': query});
  final response = await request.send();

  await for (final chunk in response.stream.transform(utf8.decoder)) {
    yield chunk;
  }
}

// Classes
class Message {
  final String id;
  final String content;
  final DateTime createdAt;
  final MessageRole role;

  const Message({
    required this.id,
    required this.content,
    required this.createdAt,
    required this.role,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'] as String,
      content: json['content'] as String,
      createdAt: DateTime.parse(json['created_at']),
      role: MessageRole.values.byName(json['role']),
    );
  }
}

enum MessageRole { user, assistant, system }
```

---

## 2. Flutter Widget Tree

Semua yang ada di Flutter adalah Widget. Widget bersifat immutable dan deklaratif.

```
App
└── MaterialApp / CupertinoApp
    └── Scaffold
        ├── AppBar
        ├── body: Column
        │   ├── Expanded (ListView)
        │   │   └── MessageBubble (custom widget)
        │   └── ChatInputBar (custom widget)
        └── floatingActionButton
```

### StatelessWidget vs StatefulWidget
```dart
// StatelessWidget — tidak punya internal state
class MessageBubble extends StatelessWidget {
  final Message message;
  final bool isCurrentUser;

  const MessageBubble({
    super.key,
    required this.message,
    required this.isCurrentUser,
  });

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isCurrentUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 12),
        padding: const EdgeInsets.all(12),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        decoration: BoxDecoration(
          color: isCurrentUser
              ? Theme.of(context).colorScheme.primary
              : Theme.of(context).colorScheme.surfaceVariant,
          borderRadius: BorderRadius.circular(16),
        ),
        child: SelectableText(
          message.content,
          style: TextStyle(
            color: isCurrentUser
                ? Theme.of(context).colorScheme.onPrimary
                : Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}

// StatefulWidget — punya mutable state
class ChatInputBar extends StatefulWidget {
  final void Function(String query) onSend;

  const ChatInputBar({super.key, required this.onSend});

  @override
  State<ChatInputBar> createState() => _ChatInputBarState();
}

class _ChatInputBarState extends State<ChatInputBar> {
  final _controller = TextEditingController();
  bool _isEmpty = true;

  @override
  void initState() {
    super.initState();
    _controller.addListener(() {
      final newEmpty = _controller.text.isEmpty;
      if (newEmpty != _isEmpty) {
        setState(() => _isEmpty = newEmpty);
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose(); // PENTING: selalu dispose controller
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 12, right: 12, bottom: MediaQuery.of(context).viewInsets.bottom + 8,
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _controller,
              maxLines: null,
              decoration: const InputDecoration(
                hintText: 'Tanya SIDIX...',
                border: OutlineInputBorder(),
              ),
              textInputAction: TextInputAction.send,
              onSubmitted: _handleSend,
            ),
          ),
          const SizedBox(width: 8),
          IconButton.filled(
            onPressed: _isEmpty ? null : () => _handleSend(_controller.text),
            icon: const Icon(Icons.send),
          ),
        ],
      ),
    );
  }

  void _handleSend(String text) {
    if (text.trim().isEmpty) return;
    widget.onSend(text.trim());
    _controller.clear();
  }
}
```

---

## 3. Flutter State Management

### Perbandingan Solusi State Management

| Solusi | Kompleksitas | Boilerplate | Reaktivitas | Use Case |
|--------|-------------|-------------|-------------|----------|
| `setState` | Sangat rendah | Minimal | Lokal saja | Widget sederhana |
| `Provider` | Rendah | Sedikit | Seluruh subtree | App medium |
| **Riverpod** | Medium | Medium | Seluruh app | App modern (recommended) |
| **BLoC** | Tinggi | Banyak | Seluruh app | Enterprise/complex |
| GetX | Rendah | Minimal | Seluruh app | Rapid prototype |

### Riverpod — Modern State Management
```dart
// providers.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

// Simple provider
final themeProvider = StateProvider<ThemeMode>((ref) => ThemeMode.system);

// AsyncNotifierProvider — untuk async state
final messagesProvider = AsyncNotifierProvider<MessagesNotifier, List<Message>>(
  MessagesNotifier.new,
);

class MessagesNotifier extends AsyncNotifier<List<Message>> {
  @override
  Future<List<Message>> build() async {
    return _fetchMessages();
  }

  Future<List<Message>> _fetchMessages() async {
    final api = ref.read(apiClientProvider);
    return api.getMessages();
  }

  Future<void> sendMessage(String query) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final api = ref.read(apiClientProvider);
      final newMsg = await api.sendQuery(query);
      final currentMessages = state.valueOrNull ?? [];
      return [...currentMessages, newMsg];
    });
  }
}

// UI
class ChatScreen extends ConsumerWidget {
  const ChatScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final messagesAsync = ref.watch(messagesProvider);

    return messagesAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, stack) => Center(child: Text('Error: $err')),
      data: (messages) => Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: messages.length,
              itemBuilder: (ctx, i) => MessageBubble(
                message: messages[i],
                isCurrentUser: messages[i].role == MessageRole.user,
              ),
            ),
          ),
          ChatInputBar(
            onSend: (q) => ref.read(messagesProvider.notifier).sendMessage(q),
          ),
        ],
      ),
    );
  }
}
```

### BLoC Pattern
```dart
// events
abstract class ChatEvent {}
class SendMessageEvent extends ChatEvent {
  final String query;
  SendMessageEvent(this.query);
}

// states
abstract class ChatState {}
class ChatInitial extends ChatState {}
class ChatLoading extends ChatState {}
class ChatLoaded extends ChatState {
  final List<Message> messages;
  ChatLoaded(this.messages);
}
class ChatError extends ChatState {
  final String message;
  ChatError(this.message);
}

// bloc
class ChatBloc extends Bloc<ChatEvent, ChatState> {
  final ApiClient _api;

  ChatBloc(this._api) : super(ChatInitial()) {
    on<SendMessageEvent>(_onSendMessage);
  }

  Future<void> _onSendMessage(
    SendMessageEvent event,
    Emitter<ChatState> emit,
  ) async {
    emit(ChatLoading());
    try {
      final msg = await _api.sendQuery(event.query);
      final current = state is ChatLoaded ? (state as ChatLoaded).messages : [];
      emit(ChatLoaded([...current, msg]));
    } catch (e) {
      emit(ChatError(e.toString()));
    }
  }
}
```

---

## 4. Flutter Navigator 2.0 & Platform Channels

### Navigator 2.0 (GoRouter)
```dart
// router.dart
import 'package:go_router/go_router.dart';

final router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
    ),
    GoRoute(
      path: '/chat/:sessionId',
      builder: (context, state) {
        final sessionId = state.pathParameters['sessionId']!;
        return ChatScreen(sessionId: sessionId);
      },
    ),
    GoRoute(
      path: '/settings',
      builder: (context, state) => const SettingsScreen(),
    ),
  ],
);

// Usage
context.go('/chat/session-123');
context.push('/settings');
context.pop();
```

### Platform Channels — Communicate dengan Native
```dart
// Dart side
import 'package:flutter/services.dart';

class BiometricService {
  static const _channel = MethodChannel('com.sidix/biometric');

  static Future<bool> authenticate() async {
    try {
      final result = await _channel.invokeMethod<bool>('authenticate', {
        'reason': 'Konfirmasi identitas untuk mengakses SIDIX',
      });
      return result ?? false;
    } on PlatformException catch (e) {
      debugPrint('Biometric error: ${e.message}');
      return false;
    }
  }
}
```

```kotlin
// Android side (MainActivity.kt)
class MainActivity : FlutterActivity() {
  override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
    super.configureFlutterEngine(flutterEngine)

    MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "com.sidix/biometric")
      .setMethodCallHandler { call, result ->
        when (call.method) {
          "authenticate" -> {
            val reason = call.argument<String>("reason") ?: ""
            authenticateWithBiometric(reason, result)
          }
          else -> result.notImplemented()
        }
      }
  }
}
```

---

## 5. React Native — Overview

React Native memungkinkan build app mobile dengan React dan JavaScript, di-bridge ke native components.

### JSX Bridge Architecture
```
JavaScript Thread     ←→ Bridge (JSON serialized) ←→ Native Thread
[React Components]                                   [iOS/Android Views]
[Business Logic]                                     [Native APIs]
[Redux/Zustand]                                      [GPU Rendering]
```

Sejak React Native 0.71+, **New Architecture** menggantikan Bridge dengan **JSI (JavaScript Interface)** yang synchronous dan lebih cepat.

### Basic Components
```jsx
import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, TextInput, FlatList, TouchableOpacity,
  KeyboardAvoidingView, Platform, StyleSheet, ActivityIndicator
} from 'react-native';

function ChatScreen() {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const flatListRef = useRef(null);

  const sendMessage = async () => {
    if (!query.trim()) return;
    const userMsg = { id: Date.now(), role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setIsLoading(true);

    try {
      const res = await fetch('http://192.168.1.x:8765/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ q: query })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', content: data.answer }]);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={item => item.id.toString()}
        renderItem={({ item }) => (
          <View style={[
            styles.bubble,
            item.role === 'user' ? styles.userBubble : styles.aiBubble
          ]}>
            <Text style={styles.bubbleText}>{item.content}</Text>
          </View>
        )}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
      />

      {isLoading && <ActivityIndicator size="small" color="#1a73e8" />}

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={query}
          onChangeText={setQuery}
          placeholder="Tanya SIDIX..."
          multiline
          returnKeyType="send"
          onSubmitEditing={sendMessage}
        />
        <TouchableOpacity
          style={[styles.sendBtn, !query.trim() && styles.sendBtnDisabled]}
          onPress={sendMessage}
          disabled={!query.trim() || isLoading}
        >
          <Text style={styles.sendBtnText}>Kirim</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  bubble: { margin: 8, padding: 12, borderRadius: 16, maxWidth: '75%' },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#1a73e8' },
  aiBubble: { alignSelf: 'flex-start', backgroundColor: '#e8eaed' },
  bubbleText: { fontSize: 16 },
  inputRow: { flexDirection: 'row', padding: 8, gap: 8 },
  input: { flex: 1, borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 8 },
  sendBtn: { backgroundColor: '#1a73e8', borderRadius: 8, padding: 10, justifyContent: 'center' },
  sendBtnDisabled: { opacity: 0.5 },
  sendBtnText: { color: 'white', fontWeight: '600' },
});
```

### Expo vs Bare Workflow

| Aspek | Expo Managed | Expo Bare | React Native CLI |
|-------|-------------|-----------|-----------------|
| Setup | Zero-config | Semi-managed | Manual |
| Native code | Tidak bisa | Bisa | Penuh |
| OTA updates | Ya (EAS Update) | Ya | Tidak |
| App size | Lebih besar | Medium | Minimal |
| Cocok untuk | Prototype, kebanyakan apps | Apps butuh native modules | Full control |

```bash
# Expo managed
npx create-expo-app sidix-mobile --template blank-typescript

# Expo dengan bare workflow
npx create-expo-app sidix-mobile --template bare-minimum

# React Native CLI
npx react-native@latest init SidixMobile --template react-native-template-typescript
```

### React Navigation
```jsx
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function TabNavigator() {
  return (
    <Tab.Navigator>
      <Tab.Screen name="Chat" component={ChatScreen} />
      <Tab.Screen name="History" component={HistoryScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Main" component={TabNavigator} options={{ headerShown: false }} />
        <Stack.Screen name="SessionDetail" component={SessionDetailScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

---

## 6. Perbandingan Flutter vs React Native vs Native

| Aspek | Flutter | React Native | Native (Swift/Kotlin) |
|-------|---------|-------------|----------------------|
| **Bahasa** | Dart | JavaScript/TypeScript | Swift / Kotlin |
| **Performance** | Sangat baik | Baik (New Arch) | Terbaik |
| **UI Rendering** | Own engine (Skia/Impeller) | Native components | Native components |
| **Code Sharing** | ~95% | ~85% | 0% |
| **Ekosistem** | Growing | Mature | Platform-specific |
| **Hot Reload** | Ya | Ya | Partial |
| **Web Support** | Ya (experimental) | Ya (React Native Web) | Tidak |
| **Learning Curve** | Dart baru | JS familiar | 2 bahasa |
| **Bundle Size** | ~5-10MB | ~3-7MB | ~1-3MB |
| **Cocok untuk** | UI-heavy, cross-platform | Web devs masuk mobile | Max performance |

---

## 7. Mobile UX Patterns

### Bottom Navigation
```dart
// Flutter bottom navigation
class SidixApp extends StatefulWidget {
  const SidixApp({super.key});

  @override
  State<SidixApp> createState() => _SidixAppState();
}

class _SidixAppState extends State<SidixApp> {
  int _selectedIndex = 0;

  final _screens = [
    const ChatScreen(),
    const HistoryScreen(),
    const SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.chat), label: 'Chat'),
          NavigationDestination(icon: Icon(Icons.history), label: 'History'),
          NavigationDestination(icon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }
}
```

### Pull to Refresh
```dart
// Flutter
RefreshIndicator(
  onRefresh: () async {
    await ref.refresh(messagesProvider.future);
  },
  child: ListView.builder(/* ... */),
)
```

```jsx
// React Native
import { RefreshControl, FlatList } from 'react-native'
<FlatList
  refreshControl={
    <RefreshControl
      refreshing={isRefreshing}
      onRefresh={handleRefresh}
      tintColor="#1a73e8"
    />
  }
/>
```

---

## 8. State Management Cross-Platform (React Native)

### Zustand — Minimal & Powerful
```javascript
// store/chatStore.js
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import AsyncStorage from '@react-native-async-storage/async-storage'

export const useChatStore = create(
  persist(
    (set, get) => ({
      sessions: [],
      activeSessionId: null,
      messages: {},

      createSession: () => {
        const id = `session-${Date.now()}`
        set(state => ({
          sessions: [...state.sessions, { id, createdAt: new Date().toISOString() }],
          activeSessionId: id,
          messages: { ...state.messages, [id]: [] }
        }))
        return id
      },

      addMessage: (sessionId, message) => {
        set(state => ({
          messages: {
            ...state.messages,
            [sessionId]: [...(state.messages[sessionId] || []), message]
          }
        }))
      },

      getActiveMessages: () => {
        const { messages, activeSessionId } = get()
        return activeSessionId ? messages[activeSessionId] || [] : []
      }
    }),
    {
      name: 'sidix-chat-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
)
```

---

## 9. Testing Mobile

### Flutter Test
```dart
// widget_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:sidix_mobile/widgets/message_bubble.dart';

void main() {
  group('MessageBubble', () {
    testWidgets('shows message content', (tester) async {
      final msg = Message(
        id: '1',
        content: 'Apa itu BM25?',
        createdAt: DateTime.now(),
        role: MessageRole.user,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MessageBubble(message: msg, isCurrentUser: true),
          ),
        ),
      );

      expect(find.text('Apa itu BM25?'), findsOneWidget);
    });

    testWidgets('user bubble aligns right', (tester) async {
      // ... test alignment
    });
  });
}
```

### Detox — E2E untuk React Native
```javascript
// e2e/chat.test.js
describe('SIDIX Chat Flow', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  it('should send a message and receive response', async () => {
    await element(by.id('chat-input')).typeText('Apa itu RAG?');
    await element(by.id('send-button')).tap();

    await waitFor(element(by.id('ai-response')))
      .toBeVisible()
      .withTimeout(10000);

    await expect(element(by.id('ai-response'))).toBeVisible();
  });
});
```

---

## 10. CI/CD Mobile — Fastlane & GitHub Actions

### Fastlane untuk iOS
```ruby
# fastlane/Fastfile
lane :beta do
  increment_build_number(
    build_number: ENV['BUILD_NUMBER']
  )

  build_app(
    workspace: 'SidixMobile.xcworkspace',
    scheme: 'SidixMobile',
    export_method: 'ad-hoc'
  )

  upload_to_testflight(
    api_key_path: 'app_store_connect_api.json'
  )
end
```

### GitHub Actions untuk Flutter
```yaml
# .github/workflows/flutter-ci.yml
name: Flutter CI/CD

on:
  push:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.19.0'
          cache: true

      - name: Install dependencies
        run: flutter pub get

      - name: Run tests
        run: flutter test --coverage

      - name: Analyze code
        run: flutter analyze

  build-android:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.19.0'
          cache: true

      - name: Build APK
        run: flutter build apk --release

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: sidix-release.apk
          path: build/app/outputs/flutter-apk/app-release.apk
```

---

## 11. Deep Links, Push Notifications, Biometrics

### Deep Links (Flutter)
```yaml
# android/app/src/main/AndroidManifest.xml
<intent-filter android:autoVerify="true">
  <action android:name="android.intent.action.VIEW"/>
  <category android:name="android.intent.category.DEFAULT"/>
  <category android:name="android.intent.category.BROWSABLE"/>
  <data android:scheme="https" android:host="sidix.app" android:pathPrefix="/chat"/>
</intent-filter>
```

```dart
// Handle deep link di GoRouter
final router = GoRouter(
  routes: [
    GoRoute(
      path: '/chat/:sessionId',
      builder: (context, state) => ChatScreen(
        sessionId: state.pathParameters['sessionId']!,
      ),
    ),
  ],
);
// sidix.app/chat/session-123 → ChatScreen(sessionId: 'session-123')
```

### Push Notifications (Firebase Cloud Messaging)
```dart
// main.dart
import 'package:firebase_messaging/firebase_messaging.dart';

@pragma('vm:entry-point')
Future<void> _firebaseBackgroundHandler(RemoteMessage message) async {
  print('Background message: ${message.messageId}');
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();

  FirebaseMessaging.onBackgroundMessage(_firebaseBackgroundHandler);

  final fcmToken = await FirebaseMessaging.instance.getToken();
  print('FCM Token: $fcmToken');
  // Kirim token ke SIDIX server untuk targeting

  FirebaseMessaging.onMessage.listen((RemoteMessage message) {
    // Foreground notification
    showLocalNotification(message);
  });

  runApp(const SidixApp());
}
```

### Biometrics (local_auth)
```dart
import 'package:local_auth/local_auth.dart';

class BiometricAuth {
  final _auth = LocalAuthentication();

  Future<bool> canUseBiometrics() async {
    final canCheck = await _auth.canCheckBiometrics;
    final isDeviceSupported = await _auth.isDeviceSupported();
    return canCheck && isDeviceSupported;
  }

  Future<bool> authenticate() async {
    try {
      return await _auth.authenticate(
        localizedReason: 'Gunakan biometrik untuk masuk ke SIDIX',
        options: const AuthenticationOptions(
          stickyAuth: true,
          biometricOnly: false,
        ),
      );
    } catch (e) {
      return false;
    }
  }
}
```

---

## 12. Platform Considerations

### iOS App Store Guidelines (Key Points)
- **Privacy**: Harus declare semua permission di Info.plist dengan usage description
- **IAP**: 30% fee, mandatory untuk digital goods
- **Review time**: 1-3 hari kerja rata-rata
- **TestFlight**: Beta testing hingga 10.000 users

### Google Play Guidelines (Key Points)
- **Target API Level**: Harus target Android API terbaru (dalam 1 tahun dari release)
- **Data Safety**: Deklarasi semua data yang dikumpulkan
- **Review time**: Lebih cepat (beberapa jam - 1 hari)
- **Open testing**: APK bisa diupload untuk internal/alpha/beta track

### Permission Best Practices
```dart
// Minta permission hanya saat diperlukan, bukan saat startup
Future<void> requestMicrophoneForVoiceQuery() async {
  final status = await Permission.microphone.status;

  if (status.isDenied) {
    final result = await Permission.microphone.request();
    if (result.isPermanentlyDenied) {
      // Arahkan ke settings
      await openAppSettings();
    }
  }
}
```

---

## 13. Implikasi untuk SIDIX

1. **SIDIX Mobile Client**: Flutter adalah pilihan terbaik — Dart lebih type-safe, performance rendering konsisten di semua device, dan satu codebase untuk iOS + Android.

2. **API Connectivity**: App mobile query ke `http://<local-ip>:8765` untuk development, production ke domain dengan HTTPS. Gunakan environment variables via `flutter_dotenv`.

3. **Offline Support**: Zustand dengan AsyncStorage atau Riverpod dengan Hive untuk cache session history offline. User tetap bisa baca conversation lama tanpa internet.

4. **Streaming Response**: Dart `Stream` dan Flutter `StreamBuilder` sangat cocok untuk consume streaming LLM response — real-time token-by-token rendering.

5. **Push Notifications**: Notify user ketika SIDIX selesai proses background indexing atau ketika ada update knowledge base baru.

6. **Deep Links**: `sidix://chat/session-id` untuk share specific conversation, atau `sidix://search?q=query` untuk langsung query dari notifikasi.

7. **Biometrics**: Gate akses app dengan face ID / fingerprint — relevant karena SIDIX mungkin berisi data pribadi/riset sensitif.

---

## Ringkasan untuk Corpus SIDIX

Note ini mencakup Flutter (Dart basics, Widget tree, StatelessWidget/StatefulWidget, Riverpod/BLoC state management, Navigator 2.0 dengan GoRouter, Platform Channels untuk native code), React Native (JSX bridge architecture, Expo vs bare workflow, React Navigation, Zustand untuk state), perbandingan komprehensif Flutter vs RN vs native, mobile UX patterns (bottom nav, pull-to-refresh, infinite scroll), CI/CD dengan Fastlane dan GitHub Actions, serta fitur mobile lanjutan (deep links, push notifications FCM, biometrics). Semua contoh kode orientasi SIDIX Mobile Client yang connect ke brain_qa API.
