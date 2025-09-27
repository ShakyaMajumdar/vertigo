from dataclasses import dataclass
import itertools
import random
import sys
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.InputStateGlobal import inputState
from panda3d.bullet import BulletPlaneShape, BulletRigidBodyNode, BulletWorld, BulletCapsuleShape, BulletBoxShape, BulletCharacterControllerNode, BulletDebugNode, ZUp
from panda3d.core import Vec2, Vec3, CardMaker, TextureStage, DirectionalLight, AmbientLight, WindowProperties, NodePath, TextNode

id_counter = itertools.count()

@dataclass
class GameSettings:
    speed: float = 20
    sprint_speed: float = 40
    gravity: float = 2*9.81
    jump_height: float = 0.7
    jump_speed: float = 10
    mouse_sensitivity = 0.1
    forward_force_rate = 0.0001

@dataclass
class Run:
    forward_force: float = 0
    score: float = 0.0

@dataclass
class Skyscraper:
    id: int
    node_path: NodePath
    pos: Vec2
    scale: Vec3
    ttl: int
    model: NodePath
    timer_triggered: bool = False

class GameScene:
    def __init__(self, world, render, loader, camera, win, aspect2d, game_settings: GameSettings, run: Run):
        self.render = render
        self.loader = loader
        self.world = world
        self.camera = camera
        self.win = win
        self.aspect2d = aspect2d
        self.game_settings = game_settings
        self.run = run

        self.world.setGravity(Vec3(0, 0, -self.game_settings.gravity))
        debug_node = BulletDebugNode('Debug')
        debug_node.showWireframe(True)
        debug_node.showConstraints(True)
        debug_node.showBoundingBoxes(True)
        debug_node.showNormals(True)
        debug_np = self.render.attachNewNode(debug_node)
        # debug_np.show()   
        self.world.setDebugNode(debug_np.node())
        self.setup_window()
        self.setup_ui()
        self.setup_light()
        self.setup_ground()
        self.setup_player()
        self.setup_controls()
        self.setup_skyscrapers()

        # self.render.ls()
    
    def setup_ui(self):
        self.score_node = TextNode("score_node")
        self.score_node_path = self.aspect2d.attachNewNode(self.score_node)
        self.score_node_path.set_scale(0.1)
        self.score_node_path.set_pos((-1, 0, 0.75))

    def setup_collisions(self):
        self.current_collisions = set()

    def setup_window(self):
        props = WindowProperties()
        # props.setFullscreen(True)
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(props)
    
    def setup_light(self):
        dlight = DirectionalLight('dlight')
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, 0)
        self.render.setLight(dlnp)

        alight = AmbientLight('alight')
        alight.setColor((0.3, 0.3, 0.3, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

    def setup_ground(self):
        self.ground_n = BulletRigidBodyNode('Ground')
        self.ground_n.addShape(BulletPlaneShape(Vec3(0, 0, 1), 0))
        self.ground_np = self.render.attachNewNode(self.ground_n)
        self.ground_np.setPos(0, 0, 0)
        ground_cm = CardMaker('ground_card')
        ground_cm.setFrame(-500, 500, -500, 500) 
        ground_vis = self.ground_np.attachNewNode(ground_cm.generate())
        ground_vis.setHpr(0, -90, 0)   
        ground_vis.setPos(0, 0, 0) 
        ground_tex = self.loader.loadTexture("maps/grid.rgb")  
        ground_vis.setTexture(ground_tex)
        ground_vis.setTexScale(TextureStage.getDefault(), 50, 50)
        self.world.attachRigidBody(self.ground_n)
    
    def setup_player(self):
        self.player_n = BulletCharacterControllerNode(BulletCapsuleShape(1.5, 1.0, ZUp), 1.5, "Player")
        self.player_np = self.render.attachNewNode(self.player_n)
        self.player_np.setPos(0, 0, 35)
        self.player_n.setGravity(self.game_settings.gravity)
        self.player_n.setMaxJumpHeight(self.game_settings.jump_height)
        self.player_n.setJumpSpeed(self.game_settings.jump_speed)
        self.world.attachCharacter(self.player_n)

        self.camera.reparentTo(self.player_np)
        self.camera.setPos(0, 0, 0.9)  

        self.pitch = 0  
    
    def setup_controls(self):
        inputState.watchWithModifiers("forward", "w")
        inputState.watchWithModifiers("backward", "s")
        inputState.watchWithModifiers("left", "a")
        inputState.watchWithModifiers("right", "d")
        inputState.watchWithModifiers("jump", "space")
        inputState.watchWithModifiers("sprint", "shift")

    def setup_skyscrapers(self):
        home_ss_id = next(id_counter)
        home_ss = Skyscraper(
            id=home_ss_id,
            node_path=self.render.attachNewNode(BulletRigidBodyNode(f'Skyscraper#{home_ss_id}')),
            pos=Vec3(0, 0, 0),
            scale=Vec3(20, 20, 30),
            ttl=5000,
            model=self.loader.loadModel('models/box.egg')
        )
        self.skyscrapers = {home_ss_id: home_ss}
        for ss in self.skyscrapers.values():
            self.setup_skyscraper(ss)
    
    def setup_skyscraper(self, ss: Skyscraper):
        ss_shape = BulletBoxShape(ss.scale*0.5)
        ss_node = ss.node_path.node()
        ss_node.setMass(0)  
        ss_node.addShape(ss_shape)
        ss.node_path.setPos(ss.pos.x, ss.pos.y, ss.scale.z/2)
        self.world.attachRigidBody(ss_node)
        ss.model.setScale(ss.scale)
        ss.model.reparentTo(ss.node_path)
        ss.model.setPos(-ss.scale.x/2, -ss.scale.y/2, -ss.scale.z/2)

    def process_mouse(self):
        md = self.win.getPointer(0)
        x = md.getX()
        y = md.getY()

        self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2)
        dx = (x - self.win.getXSize() // 2) * self.game_settings.mouse_sensitivity
        dy = (y - self.win.getYSize() // 2) * self.game_settings.mouse_sensitivity

        self.player_np.setH(self.player_np.getH() - dx)

        self.pitch = max(-90, min(90, self.pitch - dy))
        self.camera.setP(self.pitch)

    def process_movement(self, dt):
        direction = Vec3(0, 0, 0)
        if inputState.isSet("forward"):
            direction.y += 1
        if inputState.isSet("backward"):
            direction.y -= 1
        if inputState.isSet("left"):
            direction.x -= 1
        if inputState.isSet("right"):
            direction.x += 1

        direction.y += self.run.forward_force

        direction.normalize()

        quat = self.player_np.getQuat(self.render)
        dir_world = quat.xform(direction)
        dir_world.setZ(0)
        dir_world.normalize()
        if inputState.isSet("sprint"):
            vel = dir_world * self.game_settings.sprint_speed
        else:
            vel = dir_world * self.game_settings.speed
        self.player_n.setLinearMovement(vel, False)

        if inputState.isSet("jump"):
            if self.player_n.isOnGround():
                self.player_n.doJump()

    def process_collisions(self):
        new_collisions = set()
        result = self.world.contactTest(self.player_n)
        for contact in result.getContacts():
            n0, n1 = contact.getNode0(), contact.getNode1()
            other = n1 if n0.getName() == "Player" else n0
            new_collisions.add(other.getName())
            if other.getName() not in self.current_collisions:
                if other.getName().startswith("Skyscraper"):
                    self.on_player_hit_skyscraper(other)
                elif other.getName() == "Ground":
                    self.on_player_hit_ground(other)
        self.current_collisions = new_collisions
    
    def spawn_neighbours(self, ss: Skyscraper):
        n_attempts = random.randint(1, 3)
        for _ in range(n_attempts):
            dx = random.randint(5, 10) 
            dy = random.randint(5, 10)
            sx = random.randint(5, 12)
            sy = random.randint(5, 12)
            sz = random.randint(1, 4) * 10
            if random.random() > 0.5:
                px = ss.pos.x + ss.scale.x/2 + sx/2 + dx
            else:
                px = ss.pos.x - ss.scale.x/2 - sx/2 - dx
            if random.random() > 0.5:
                py = ss.pos.y + ss.scale.y/2 + sy/2 + dy
            else:
                py = ss.pos.y - ss.scale.y/2 - sy/2 - dy

            if not self.intersects_ss(Vec2(px, py), Vec2(sx, sy)):
                ss_id = next(id_counter)
                ss = Skyscraper(
                    id=ss_id,
                    node_path=self.render.attachNewNode(BulletRigidBodyNode(f'Skyscraper#{ss_id}')),
                    pos=Vec3(px, py, 0),
                    scale=Vec3(sx, sy, sz),
                    ttl=5000,
                    model=self.loader.loadModel('models/box.egg')
                )
                self.skyscrapers[ss_id] = ss
                self.setup_skyscraper(ss)

    def intersects_ss(self, pos: Vec2, scale: Vec2):
        for other in self.skyscrapers.values():
            if (abs(pos.x - other.pos.x) * 2 < (scale.x + other.scale.x) and
                abs(pos.y - other.pos.y) * 2 < (scale.y + other.scale.y)):
                return True
        return False

    def on_player_hit_skyscraper(self, node):
        print("Player collided with skyscraper:", node.getName())
        ss = self.skyscrapers[int(node.getName().split("#")[1])]
        if not ss.timer_triggered:
            ss.timer_triggered = True
            self.spawn_neighbours(ss)

    def on_player_hit_ground(self, node):
        print("Player collided with ground:", node.getName())

    def update_skyscrapers(self):
        new_ss = {}
        for id, ss in self.skyscrapers.items():
            if ss.timer_triggered:
                ss.ttl -= 1
            if ss.ttl > 0:
                new_ss[id] = ss
            else:
                self.world.remove(ss.node_path.node())
                ss.node_path.removeNode()
        self.skyscrapers = new_ss

    def update_forward_force(self):
        self.run.forward_force += self.game_settings.forward_force_rate
    def f(self):
        p = self.player_np.getPos()
        return f"{round(p.x)} {round(p.y)} {round(p.z)}"
    def update_score(self):
        self.run.score += 0.1        
        self.score_node.set_text(f"SCORE: {round(self.run.score)} {self.f()}")

    def update(self, task):
        dt = globalClock.getDt()
        self.process_mouse()
        self.process_movement(dt)
        self.update_skyscrapers()
        self.update_forward_force()
        self.update_score()
        self.world.doPhysics(dt)
        self.process_collisions()
        return task.cont


class App(ShowBase):
    def __init__(self):
        super().__init__()
        self.accept("escape", self.exit_app)
        self.disableMouse()
        game_scene = GameScene(BulletWorld(), self.render, self.loader, self.camera, self.win, self.aspect2d, GameSettings(), Run())
        self.taskMgr.add(game_scene.update, 'update')
    
    def exit_app(self):
        sys.exit(0)

if __name__ == "__main__":
    app = App()
    app.run()
