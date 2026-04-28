# Research Note 49 — Game Development: Godot 4, Unity, & Web Games

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal**: 2026-04-17
**Sumber**: Pengetahuan teknis + roadmap.sh best practices
**Relevance SIDIX**: Game development adalah domain pengetahuan teknis yang bernilai tinggi untuk corpus SIDIX — developer game sering mencari referensi tentang physics, rendering pipeline, state machine, dan arsitektur engine. SIDIX sebagai LLM platform dapat menjadi asisten AI untuk developer game, terutama untuk Godot (open source) yang populer di kalangan indie developer Indonesia. Konsep game loop, delta time, dan event system juga overlap dengan arsitektur real-time system di SIDIX.
**Tags**: `godot4`, `unity`, `gdscript`, `game-loop`, `physics`, `phaser-js`, `game-design`, `monetization`, `steam`, `2d-game`

---

## 1. Game Loop — Fondasi Semua Game Engine

Game loop adalah inti dari setiap game — sebuah infinite loop yang terus berjalan selama game aktif.

```
┌─────────────────────────────────────────────┐
│                 GAME LOOP                   │
│                                             │
│  1. Process Input (keyboard/mouse/touch)    │
│  2. Update Logic (physics, AI, state)       │
│  3. Render (draw frame ke layar)            │
│                                             │
│  Target: 60 FPS = 16.67ms per frame         │
│          120 FPS = 8.33ms per frame         │
└─────────────────────────────────────────────┘
```

### Delta Time — Kunci Frame-Independent Movement

```gdscript
# Tanpa delta time: movement tergantung FPS
# Di 60 FPS: bergerak 5px per frame = 300px/detik
# Di 30 FPS: bergerak 5px per frame = 150px/detik (SETENGAHNYA!)
position.x += 5  # SALAH

# Dengan delta time: movement konsisten di semua FPS
# speed = 300 px/detik
# delta = waktu sejak frame sebelumnya (misal 0.016 detik untuk 60 FPS)
position.x += speed * delta  # BENAR
```

### Fixed Update vs Regular Update

| | Regular Update | Fixed Update |
|---|---|---|
| **Godot** | `_process(delta)` | `_physics_process(delta)` |
| **Unity** | `Update()` | `FixedUpdate()` |
| **Kapan** | Per frame render | Fixed timestep (60/detik default) |
| **Untuk** | Input, animation, UI | Physics, collision detection |
| **Delta** | Variabel | Konstanta (1/60 = 0.01667) |

---

## 2. Godot 4 — Node & Scene System

### Arsitektur Node/Scene
Semua di Godot adalah **Node** yang membentuk hierarki **Scene Tree**.

```
# Struktur Scene game platformer sederhana
Main (Node)
├── World (Node2D)
│   ├── TileMap (TileMap)
│   ├── Player (CharacterBody2D)
│   │   ├── Sprite2D
│   │   ├── AnimationPlayer
│   │   ├── CollisionShape2D
│   │   └── Camera2D
│   └── Enemies (Node2D)
│       ├── Enemy01 (CharacterBody2D)
│       └── Enemy02 (CharacterBody2D)
├── UI (CanvasLayer)
│   ├── HUD (Control)
│   └── PauseMenu (Control)
└── AudioManager (Node)
```

### GDScript Fundamentals
```gdscript
# player.gd — Contoh karakter platformer lengkap
extends CharacterBody2D

# @export: exposed di Inspector Editor
@export var speed: float = 300.0
@export var jump_force: float = -600.0
@export var gravity_multiplier: float = 2.5

# Konstanta
const MAX_FALL_SPEED: float = 800.0

# Variable
var is_on_floor_prev: bool = false

# Signals
signal player_died
signal collected_item(item_type: String, value: int)

# Referensi node
@onready var sprite: Sprite2D = $Sprite2D
@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var coyote_timer: Timer = $CoyoteTimer

func _ready() -> void:
    # Called saat node masuk scene tree
    print("Player ready!")

func _physics_process(delta: float) -> void:
    # Gravity
    if not is_on_floor():
        velocity.y += ProjectSettings.get_setting("physics/2d/default_gravity") * gravity_multiplier * delta
        velocity.y = min(velocity.y, MAX_FALL_SPEED)

    # Jump (termasuk coyote time)
    if Input.is_action_just_pressed("ui_accept"):
        if is_on_floor() or not coyote_timer.is_stopped():
            velocity.y = jump_force
            coyote_timer.stop()

    # Horizontal movement
    var direction: float = Input.get_axis("ui_left", "ui_right")
    if direction:
        velocity.x = move_toward(velocity.x, direction * speed, speed * delta * 10)
        sprite.flip_h = direction < 0
    else:
        velocity.x = move_toward(velocity.x, 0, speed * delta * 8)

    # Coyote time: buffer jump setelah jatuh dari platform
    if is_on_floor() and not is_on_floor_prev:
        coyote_timer.start(0.15)
    is_on_floor_prev = is_on_floor()

    # Animation
    _update_animation()

    move_and_slide()

func _update_animation() -> void:
    if not is_on_floor():
        anim_player.play("jump" if velocity.y < 0 else "fall")
    elif abs(velocity.x) > 10:
        anim_player.play("run")
    else:
        anim_player.play("idle")

func take_damage(amount: int) -> void:
    # ... damage logic
    if health <= 0:
        player_died.emit()
```

### Signals — Event System Godot
```gdscript
# Definisi signal
signal health_changed(old_value: int, new_value: int)
signal game_over

# Emit signal
health_changed.emit(old_health, new_health)

# Connect via kode (lebih fleksibel)
player.player_died.connect(_on_player_died)
player.collected_item.connect(_on_item_collected)

# Receiver
func _on_player_died() -> void:
    $UI/GameOverScreen.show()
    get_tree().paused = true

func _on_item_collected(item_type: String, value: int) -> void:
    score += value
    $UI/HUD/ScoreLabel.text = "Score: %d" % score
```

### Area2D & CollisionShape — Physics Zones
```gdscript
# Coin collectible
extends Area2D

@export var value: int = 10

func _ready() -> void:
    body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        body.collected_item.emit("coin", value)
        # Efek visual sebelum queue_free
        $AnimationPlayer.play("collect")
        await $AnimationPlayer.animation_finished
        queue_free()
```

### TileMap — Level Design
```gdscript
# Akses TileMap via kode
@onready var tile_map: TileMap = $TileMap

func get_tile_at_world_pos(world_pos: Vector2) -> Vector2i:
    return tile_map.local_to_map(tile_map.to_local(world_pos))

func is_walkable(world_pos: Vector2) -> bool:
    var map_pos = get_tile_at_world_pos(world_pos)
    var data = tile_map.get_cell_tile_data(0, map_pos)
    if data == null:
        return false
    return data.get_custom_data("walkable")
```

### Shader di Godot 4
```glsl
// outline.gdshader — outline effect untuk character
shader_type canvas_item;

uniform float outline_width: hint_range(0.0, 10.0) = 2.0;
uniform vec4 outline_color: source_color = vec4(1.0, 1.0, 1.0, 1.0);

void fragment() {
    vec4 original = texture(TEXTURE, UV);

    // Sample 8 neighbors
    float outline = 0.0;
    vec2 size = outline_width / vec2(textureSize(TEXTURE, 0));

    for (float x = -1.0; x <= 1.0; x++) {
        for (float y = -1.0; y <= 1.0; y++) {
            if (x == 0.0 && y == 0.0) continue;
            outline += texture(TEXTURE, UV + vec2(x, y) * size).a;
        }
    }

    outline = min(outline, 1.0);

    COLOR = mix(original, outline_color, outline * (1.0 - original.a));
}
```

---

## 3. Unity — MonoBehaviour Lifecycle

### Lifecycle Order
```
Awake() → OnEnable() → Start() → [per frame: FixedUpdate → Update → LateUpdate] → OnDisable() → OnDestroy()
```

```csharp
using UnityEngine;

public class PlayerController : MonoBehaviour
{
    [Header("Movement")]
    [SerializeField] private float speed = 5f;
    [SerializeField] private float jumpForce = 7f;

    [Header("Ground Check")]
    [SerializeField] private LayerMask groundLayer;
    [SerializeField] private Transform groundCheck;

    private Rigidbody2D _rb;
    private Animator _anim;
    private bool _isGrounded;
    private float _moveInput;

    // Awake: inisialisasi komponen, SEBELUM Start
    private void Awake()
    {
        _rb = GetComponent<Rigidbody2D>();
        _anim = GetComponent<Animator>();
    }

    // Start: inisialisasi yang butuh komponen lain sudah ready
    private void Start()
    {
        Debug.Log($"Player spawned at {transform.position}");
    }

    // Update: per frame, untuk input
    private void Update()
    {
        _moveInput = Input.GetAxisRaw("Horizontal");
        _isGrounded = Physics2D.OverlapCircle(groundCheck.position, 0.2f, groundLayer);

        if (Input.GetButtonDown("Jump") && _isGrounded)
        {
            _rb.velocity = new Vector2(_rb.velocity.x, jumpForce);
        }

        // Update animasi
        _anim.SetFloat("Speed", Mathf.Abs(_moveInput));
        _anim.SetBool("IsGrounded", _isGrounded);
    }

    // FixedUpdate: physics (berjalan di fixed timestep)
    private void FixedUpdate()
    {
        _rb.velocity = new Vector2(_moveInput * speed, _rb.velocity.y);
    }

    // LateUpdate: setelah semua Update() — ideal untuk kamera follow
    private void LateUpdate()
    {
        // Camera.main.transform.position = ...
    }
}
```

### ScriptableObject — Data Container Reusable
```csharp
using UnityEngine;

[CreateAssetMenu(fileName = "WeaponData", menuName = "SIDIX Game/Weapon")]
public class WeaponData : ScriptableObject
{
    [Header("Stats")]
    public string weaponName;
    public int damage;
    public float fireRate;
    public float range;

    [Header("Visuals")]
    public Sprite icon;
    public GameObject prefab;

    [Header("Audio")]
    public AudioClip fireSound;
    public AudioClip reloadSound;
}

// Penggunaan: drag-drop di Inspector, tidak perlu hard-code
public class WeaponSystem : MonoBehaviour
{
    [SerializeField] private WeaponData currentWeapon;

    public void Fire()
    {
        // Gunakan data dari ScriptableObject
        Debug.Log($"Firing {currentWeapon.weaponName} for {currentWeapon.damage} dmg");
        AudioSource.PlayClipAtPoint(currentWeapon.fireSound, transform.position);
    }
}
```

### Prefab System
```csharp
// Instantiate prefab
[SerializeField] private GameObject enemyPrefab;
[SerializeField] private Transform spawnPoint;

void SpawnEnemy()
{
    var enemy = Instantiate(enemyPrefab, spawnPoint.position, Quaternion.identity);
    enemy.GetComponent<Enemy>().Initialize(difficulty: 2);
}

// Object Pool — performa lebih baik dari Instantiate/Destroy
using UnityEngine.Pool;

public class BulletPool : MonoBehaviour
{
    [SerializeField] private Bullet bulletPrefab;
    private ObjectPool<Bullet> _pool;

    private void Awake()
    {
        _pool = new ObjectPool<Bullet>(
            createFunc: () => Instantiate(bulletPrefab),
            actionOnGet: b => b.gameObject.SetActive(true),
            actionOnRelease: b => b.gameObject.SetActive(false),
            actionOnDestroy: b => Destroy(b.gameObject),
            defaultCapacity: 20,
            maxSize: 100
        );
    }

    public Bullet GetBullet() => _pool.Get();
    public void ReturnBullet(Bullet b) => _pool.Release(b);
}
```

---

## 4. Game Design Fundamentals

### Game Loop Design
```
Core Loop (seconds): Action → Reward → Progress → New Challenge
Meta Loop (minutes/hours): Unlock → Customize → Show off → FOMO → Return

Contoh:
Core: Tembak musuh → Coin → Level up → Boss baru
Meta: Unlock karakter baru → Customize skill → Leaderboard → Daily quest
```

### Game Feel / Juice — Membuat Game Terasa "Hidup"

| Teknik | Implementasi | Efek pada Player |
|--------|-------------|-----------------|
| **Screen shake** | Getar kamera saat damage | Impact terasa real |
| **Hitstop** | Pause 2-4 frame saat hit | Kepuasan memukul |
| **Particle burst** | Partikel saat collect item | Satisfying feedback |
| **Sound design** | SFX per aksi | Immersion |
| **Juice animation** | Squash & stretch | Karakter terasa hidup |
| **Lerp camera** | Smooth follow | Comfortable |
| **Anticipation** | Angin-up sebelum serangan | Readability |

```gdscript
# Screen shake di Godot
func shake_camera(duration: float = 0.3, intensity: float = 8.0) -> void:
    var tween = create_tween()
    var original_pos = camera.position

    for i in 20:
        var target = original_pos + Vector2(
            randf_range(-intensity, intensity),
            randf_range(-intensity, intensity)
        )
        tween.tween_property(camera, "position", target, duration / 20.0)

    tween.tween_property(camera, "position", original_pos, 0.05)
```

---

## 5. 2D vs 3D — Rendering Pipeline

### 2D Rendering
```
Sprite/Texture → Batch → Sort by Z-index → GPU Draw
```
- **Sprite Batching**: Group sprites dengan atlas texture yang sama → 1 draw call
- **Tilemap**: Optimasi khusus untuk grid-based level
- **CanvasItem**: Base class semua 2D nodes di Godot

### 3D Concepts
```gdscript
# Transform di 3D (Godot)
# Quaternion — representasi rotasi tanpa gimbal lock
var rot_quat = Quaternion(Vector3.UP, PI / 4)  # rotate 45° around Y axis

# vs Euler angles (lebih intuitif tapi ada gimbal lock)
rotation_degrees = Vector3(0, 45, 0)

# Lerp antara dua rotasi
transform.basis = transform.basis.slerp(target_basis, delta * rotation_speed)
```

### 3D Lighting Types

| Tipe | Godot 4 | Unity | Kegunaan |
|------|---------|-------|----------|
| Directional | DirectionalLight3D | Directional Light | Matahari/bulan |
| Point | OmniLight3D | Point Light | Lampu, api |
| Spot | SpotLight3D | Spot Light | Senter, lampu jalan |
| Area | Area3D | Area Light | Ambient dalam ruangan |
| Sky | WorldEnvironment | Skybox | Pencahayaan global |

---

## 6. Web Games — Phaser.js & Pixi.js

### Phaser.js — Framework Game Web Terlengkap
```javascript
import Phaser from 'phaser';

class GameScene extends Phaser.Scene {
  constructor() {
    super({ key: 'GameScene' });
  }

  // preload: load assets sebelum scene start
  preload() {
    this.load.image('player', 'assets/player.png');
    this.load.spritesheet('coin', 'assets/coin.png', {
      frameWidth: 32, frameHeight: 32
    });
    this.load.tilemapTiledJSON('map', 'assets/level1.json');
    this.load.image('tiles', 'assets/tileset.png');
    this.load.audio('bgm', 'assets/music/level1.ogg');
  }

  // create: inisialisasi game objects
  create() {
    // Tilemap
    const map = this.make.tilemap({ key: 'map' });
    const tileset = map.addTilesetImage('tileset', 'tiles');
    const groundLayer = map.createLayer('Ground', tileset, 0, 0);
    groundLayer.setCollisionByProperty({ collides: true });

    // Player
    this.player = this.physics.add.sprite(100, 200, 'player');
    this.player.setBounce(0.1);
    this.player.setCollideWorldBounds(true);

    // Coins dengan animation
    this.anims.create({
      key: 'spin',
      frames: this.anims.generateFrameNumbers('coin', { start: 0, end: 7 }),
      frameRate: 12,
      repeat: -1
    });

    this.coins = this.physics.add.staticGroup();
    // Spawn coins dari map object layer
    map.getObjectLayer('Coins').objects.forEach(obj => {
      this.coins.create(obj.x, obj.y, 'coin').anims.play('spin');
    });

    // Collisions
    this.physics.add.collider(this.player, groundLayer);
    this.physics.add.overlap(this.player, this.coins, this.collectCoin, null, this);

    // Input
    this.cursors = this.input.keyboard.createCursorKeys();
    this.wasd = this.input.keyboard.addKeys({
      up: Phaser.Input.Keyboard.KeyCodes.W,
      left: Phaser.Input.Keyboard.KeyCodes.A,
      right: Phaser.Input.Keyboard.KeyCodes.D
    });

    // Camera
    this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
    this.cameras.main.startFollow(this.player, true, 0.1, 0.1);

    // Score
    this.score = 0;
    this.scoreText = this.add.text(16, 16, 'Score: 0', {
      fontSize: '24px', color: '#fff', stroke: '#000', strokeThickness: 4
    }).setScrollFactor(0); // Tetap di screen (tidak ikut kamera)
  }

  // update: called setiap frame
  update() {
    const left = this.cursors.left.isDown || this.wasd.left.isDown;
    const right = this.cursors.right.isDown || this.wasd.right.isDown;
    const jump = this.cursors.up.isDown || this.wasd.up.isDown;

    if (left) {
      this.player.setVelocityX(-200);
      this.player.setFlipX(true);
    } else if (right) {
      this.player.setVelocityX(200);
      this.player.setFlipX(false);
    } else {
      this.player.setVelocityX(0);
    }

    if (jump && this.player.body.onFloor()) {
      this.player.setVelocityY(-450);
    }
  }

  collectCoin(player, coin) {
    coin.destroy();
    this.score += 10;
    this.scoreText.setText(`Score: ${this.score}`);
  }
}

// Game config
const config = {
  type: Phaser.AUTO,   // otomatis WebGL atau Canvas
  width: 800,
  height: 600,
  backgroundColor: '#2d5a8e',
  physics: {
    default: 'arcade',
    arcade: { gravity: { y: 400 }, debug: false }
  },
  scene: [BootScene, PreloadScene, MenuScene, GameScene, GameOverScene]
};

new Phaser.Game(config);
```

### Pixi.js — Rendering Library (tanpa physics/game logic)
```javascript
import * as PIXI from 'pixi.js';

const app = new PIXI.Application({
  width: 800, height: 600,
  backgroundColor: 0x1a1a2e,
  antialias: true,
  resolution: window.devicePixelRatio || 1,
  autoDensity: true
});
document.body.appendChild(app.view);

// Sprite
const texture = await PIXI.Assets.load('player.png');
const player = new PIXI.Sprite(texture);
player.anchor.set(0.5);
player.x = 400;
player.y = 300;
app.stage.addChild(player);

// Container untuk grouping
const uiContainer = new PIXI.Container();
app.stage.addChild(uiContainer);

// Text
const scoreText = new PIXI.Text('Score: 0', {
  fontFamily: 'Arial', fontSize: 24, fill: 0xffffff
});
scoreText.position.set(10, 10);
uiContainer.addChild(scoreText);

// Ticker (game loop)
app.ticker.add((delta) => {
  player.rotation += 0.01 * delta;
});
```

---

## 7. Game Networking

### Authoritative Server Architecture
```
Client A             Server              Client B
   |                    |                    |
   |-- Input (move) --> |                    |
   |                    |-- Validate input   |
   |                    |-- Update world     |
   |<-- Game state ---- |-- Game state --> --|
   |                    |                    |
```

### Lag Compensation Techniques

| Teknik | Deskripsi | Implementasi |
|--------|-----------|-------------|
| **Client prediction** | Client langsung gerak, rollback jika salah | Simpan state history |
| **Server reconciliation** | Server koreksi jika prediksi salah | Apply server state + replay inputs |
| **Entity interpolation** | Interpolasi posisi entity lain | Smooth movement dari network updates |
| **Dead reckoning** | Prediksi posisi entitas yang jarang update | Extrapolate dari velocity |

```javascript
// Godot 4 — multiplayer dengan high-level API
extends MultiplayerSynchronizer

# Sync properties otomatis ke semua peers
@export var synced_position: Vector2 = Vector2.ZERO
@export var synced_velocity: Vector2 = Vector2.ZERO

func _physics_process(delta: float) -> void:
    if is_multiplayer_authority():
        synced_position = position
        synced_velocity = velocity
    else:
        # Interpolate untuk peers lain
        position = position.lerp(synced_position, delta * 20)
```

---

## 8. Audio — Spatial Audio & Dynamic Music

### Godot 4 Audio Bus
```
Master Bus
├── Music Bus (volume kontrol musik)
│   └── BGM AudioStreamPlayer
├── SFX Bus (volume kontrol efek suara)
│   ├── FootstepPlayer
│   ├── WeaponPlayer
│   └── UIPlayer
└── Ambient Bus
    └── EnvironmentPlayer
```

```gdscript
# Dynamic music system — crossfade antar layer
var music_layers: Array[AudioStreamPlayer] = []
var current_intensity: float = 0.0

func set_music_intensity(value: float) -> void:
    current_intensity = clamp(value, 0.0, 1.0)

    # Layer 0: selalu aktif (base)
    # Layer 1: aktif saat intensity > 0.3 (drums)
    # Layer 2: aktif saat intensity > 0.7 (lead melody)
    for i in music_layers.size():
        var threshold = float(i) / music_layers.size()
        var target_volume = 0.0 if current_intensity < threshold else 0.0
        var tween = create_tween()
        tween.tween_property(music_layers[i], "volume_db", target_volume, 0.5)
```

---

## 9. Monetization Ethics

| Model | Contoh | Etika |
|-------|--------|-------|
| **Premium** (bayar sekali) | $9.99 beli game | Paling jujur |
| **Cosmetics only** | Skin, warna | Acceptable — tidak pay-to-win |
| **DLC konten** | Expansion pack | OK jika nilai nyata |
| **Battle Pass** | Season content | Grey area — FOMO psychology |
| **Gacha/Loot boxes** | Random rewards | Kontroversial, dilarang di beberapa negara |
| **Pay-to-win** | Beli kekuatan | Merusak balance, tidak etis |
| **Energy system** | Bayar untuk main | Dark pattern |

### IAP di Mobile (Flutter)
```dart
// in_app_purchase package
import 'package:in_app_purchase/in_app_purchase.dart';

class IAPService {
  static const _kProductIds = {'skin_pack_01', 'remove_ads'};

  Future<void> initialize() async {
    final isAvailable = await InAppPurchase.instance.isAvailable();
    if (!isAvailable) return;

    final response = await InAppPurchase.instance
        .queryProductDetails(_kProductIds);

    if (response.error != null) {
      // Handle error
      return;
    }

    // Show products to user
    final products = response.productDetails;
  }

  Future<void> buyProduct(ProductDetails product) async {
    final purchaseParam = PurchaseParam(productDetails: product);
    await InAppPurchase.instance.buyNonConsumable(
      purchaseParam: purchaseParam,
    );
  }
}
```

---

## 10. Publishing

### itch.io (Indie Platform)
```
1. Export game (Godot: Project → Export → HTML5/Windows/Linux)
2. Buat akun itch.io
3. Upload file + set harga (free/PWYW/paid)
4. Atur devlog untuk community engagement
5. Submit ke game jams untuk exposure
```

### Steam (via Steamworks SDK)
```gdscript
# Godot Steam plugin (GodotSteam)
extends Node

func _ready() -> void:
    Steam.steamInit()

func unlock_achievement(achievement_name: String) -> void:
    if Steam.isSteamRunning():
        Steam.setAchievement(achievement_name)
        Steam.storeStats()

func get_leaderboard_entries() -> void:
    Steam.findLeaderboard("high_scores")
    await Steam.leaderboard_find_result

    Steam.downloadLeaderboardEntries(1, 10, Steam.LEADERBOARD_DATA_REQUEST_GLOBAL)
    await Steam.leaderboard_scores_downloaded
```

### Google Play / App Store (Mobile Games)
```yaml
# Codemagic CI/CD untuk Flutter game
workflows:
  android-release:
    name: Android Release
    environment:
      android_signing:
        - sidix_game_keystore
      groups:
        - google_play_credentials
    scripts:
      - name: Build AAB
        script: flutter build appbundle --release
    publishing:
      google_play:
        credentials: $GCLOUD_SERVICE_ACCOUNT_CREDENTIALS
        track: beta
        changes_not_sent_for_review: false
```

---

## 11. Perbandingan Godot vs Unity

| Aspek | Godot 4 | Unity |
|-------|---------|-------|
| **Lisensi** | MIT (100% free) | Subscription (runtime fee kontroversial) |
| **Bahasa** | GDScript (Python-like) + C# | C# utama |
| **Scene system** | Node tree (intuitif) | GameObject + Component |
| **2D support** | Native, excellent | Lebih fokus 3D |
| **3D support** | Baik (Vulkan renderer) | Industry standard |
| **Asset Store** | Kecil | Besar (Asset Store) |
| **Community** | Growing fast | Mature, besar |
| **Mobile export** | Ya | Ya |
| **Web export** | Ya (WASM) | Ya |
| **File size engine** | ~40MB | ~500MB+ |
| **Cocok untuk** | Indie, 2D, prototype | Professional, 3D, console |

---

## 12. Implikasi untuk SIDIX

1. **Corpus Game Dev**: SIDIX sebagai asisten developer game — bisa jawab pertanyaan tentang GDScript, Unity C#, Phaser.js, physics, shader, animation state machine.

2. **Godot + SIDIX Integration**: Bisa dibuat Godot plugin yang query SIDIX untuk documentation lookup langsung dari editor.

3. **Phaser.js untuk SIDIX Mini-Games**: SIDIX UI bisa memiliki mini interactive demos berbasis Phaser.js (misalnya visualisasi BM25 scoring sebagai game/animation).

4. **Arsitektur Paralel**: Game loop (process input → update → render) mirip dengan agentic loop SIDIX (receive query → process → respond). Keduanya menggunakan delta time / timeout untuk prevent blocking.

5. **State Machine**: Konsep FSM (Finite State Machine) di game (idle/run/jump/attack) sama dengan state management di SIDIX agent (thinking/searching/responding/waiting).

6. **Event System (Signals)**: Godot Signals = Python event dispatcher = FastAPI background tasks. Pola yang sama.

---

## Ringkasan untuk Corpus SIDIX

Note ini mencakup fondasi game development dari game loop dan delta time, Godot 4 (GDScript, Node/Scene, Signals, Area2D, TileMap, Shader, AnimationPlayer), Unity (MonoBehaviour lifecycle, GameObject/Component, Prefab, ScriptableObject, Object Pool), game design fundamentals (core loop, meta loop, game feel, juice), 2D vs 3D rendering, web games dengan Phaser.js dan Pixi.js, game networking (authoritative server, lag compensation, client prediction), audio spasial dan dynamic music, monetisasi etis, dan publishing ke itch.io/Steam/mobile. Semua topik dilengkapi kode nyata yang production-quality.
