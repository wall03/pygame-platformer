import pygame
import math

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

frame_time = 60

# for dashing
min_cooldown = 800
max_cooldown = 1300
current_cooldown = min_cooldown
last_dash = -min_cooldown

paused_until = 0
player_radius = 40
hit_stun_ms = 120

is_charging = False
charge_start_ms = 0
max_charge_ms = 400
min_dash_speed = 1200
max_dash_speed = 6000
dash_requested = False
freeze_available = False

space_held = False

player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
player_momentum = pygame.Vector2(0, 0)
player_angle = 0 #radians

#borundries
boundries = [
    ((0,0),(0,screen.get_height()-1)),
    ((0,0),(screen.get_width()-1,0)),
    ((screen.get_width()-1,0),(screen.get_width()-1,screen.get_height()-1)),
    ((0,screen.get_height()-1),(screen.get_width()-1,screen.get_height()-1))
]
initial_boundries = boundries.copy()

#bounciness of each line
initial_bouncy_boundries = [
    0.8,
    0.8,
    0.8,
    0.8,
]
bouncy_boundries = initial_bouncy_boundries.copy()


def draw_arrow(
        surface: pygame.Surface,
        start: pygame.Vector2,
        end: pygame.Vector2,
        color: pygame.Color,
        body_width: int = 2,
        head_width: int = 4,
        head_height: int = 2,
    ):
    """Draw an arrow between start and end with the arrow head at the end.

    Args:
        surface (pygame.Surface): The surface to draw on
        start (pygame.Vector2): Start position
        end (pygame.Vector2): End position
        color (pygame.Color): Color of the arrow
        body_width (int, optional): Defaults to 2.
        head_width (int, optional): Defaults to 4.
        head_height (float, optional): Defaults to 2.
    """
    arrow = start - end
    angle = arrow.angle_to(pygame.Vector2(0, -1))
    body_length = arrow.length() - head_height

    # Create the triangle head around the origin
    head_verts = [
        pygame.Vector2(0, head_height / 2),  # Center
        pygame.Vector2(head_width / 2, -head_height / 2),  # Bottomright
        pygame.Vector2(-head_width / 2, -head_height / 2),  # Bottomleft
    ]
    # Rotate and translate the head into place
    translation = pygame.Vector2(0, arrow.length() - (head_height / 2)).rotate(-angle)
    for i in range(len(head_verts)):
        head_verts[i].rotate_ip(-angle)
        head_verts[i] += translation
        head_verts[i] += start

    pygame.draw.polygon(surface, color, head_verts)

    # Stop weird shapes when the arrow is shorter than arrow head
    if arrow.length() >= head_height:
        # Calculate the body rect, rotate and translate into place
        body_verts = [
            pygame.Vector2(-body_width / 2, body_length / 2),  # Topleft
            pygame.Vector2(body_width / 2, body_length / 2),  # Topright
            pygame.Vector2(body_width / 2, -body_length / 2),  # Bottomright
            pygame.Vector2(-body_width / 2, -body_length / 2),  # Bottomleft
        ]
        translation = pygame.Vector2(0, body_length / 2).rotate(-angle)
        for i in range(len(body_verts)):
            body_verts[i].rotate_ip(-angle)
            body_verts[i] += translation
            body_verts[i] += start

        pygame.draw.polygon(surface, color, body_verts)

    
while running:
    current_ticks = pygame.time.get_ticks()

    # poll for events
    for event in pygame.event.get():
        # pygame.QUIT event means the user clicked X to close your window
        if event.type == pygame.QUIT:
            running = False

        # if space is pressed, start charging if off cooldown, otherwise mark as held to start charging immediately when it comes off cooldown
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if current_ticks >= last_dash + current_cooldown:
                is_charging = True
                charge_start_ms = current_ticks
            else: # if dash on cooldown, record key as held
                space_held = True

        # if space is released, either request dash if it was charging, or just mark as not held if it was on cooldown
        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            if current_ticks >= last_dash + current_cooldown and is_charging:
                space_held = False
                dash_requested = True
                is_charging = False
            if is_charging:
                dash_requested = True
                is_charging = False

    if current_ticks >= last_dash + current_cooldown and space_held and not is_charging:  # if dash just came off cooldown while space is held, start charging
        is_charging = True
        charge_start_ms = current_ticks

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("purple")
    pygame.draw.circle(screen, "blue", player_pos, player_radius)

    for line in boundries:
        pygame.draw.line(screen,"white",*line)
    
    # direction pointing in radians
    direction = math.atan2(player_momentum.y, player_momentum.x)
    player_angle = direction

    # for movement
    acceleration = 1200
    drag = 2.8

    
    new_player_pos = player_pos.copy()
    new_player_angle = player_angle
    hit_wall = False
    if current_ticks >= paused_until:
        # Frame-rate independent drag.
        player_momentum -= player_momentum * drag * dt

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            player_momentum.y -= acceleration * dt
        if keys[pygame.K_s]:
            player_momentum.y += acceleration * dt
        if keys[pygame.K_a]:
            player_momentum.x -= acceleration * dt
        if keys[pygame.K_d]:
            player_momentum.x += acceleration * dt
        if keys[pygame.K_ESCAPE]: # reset boundries created by user
            boundries = initial_boundries.copy()
            bouncy_boundries = initial_bouncy_boundries.copy()

        if dash_requested:
            hold_duration = current_ticks - charge_start_ms
            current_cooldown = min(min_cooldown + (max_cooldown - min_cooldown) * (hold_duration / max_charge_ms), max_cooldown)
            charge_ratio = min(hold_duration / max_charge_ms, 1)
            dash_speed = min_dash_speed + (max_dash_speed - min_dash_speed) * charge_ratio
            last_dash = current_ticks
            player_momentum.x += math.cos(direction) * dash_speed
            player_momentum.y += math.sin(direction) * dash_speed
            dash_requested = False
            freeze_available = True

            # add boundries that are behind and perpendicular to the player's direction for interesting stuff
            boundries.append((
                (player_radius*math.cos(direction + math.pi/2)+player_pos.x+player_radius*math.cos(direction + math.pi), 
                 player_radius*math.sin(direction + math.pi/2)+player_pos.y+player_radius*math.sin(direction + math.pi)),
                (player_radius*math.cos(direction - math.pi/2)+player_pos.x+player_radius*math.cos(direction - math.pi),
                 player_radius*math.sin(direction - math.pi/2)+player_pos.y+player_radius*math.sin(direction - math.pi))
            ))

            bouncy_boundries.append(1.2)  # make these extra boundries extra bouncy for fun interactions

        new_player_angle = math.atan2(player_momentum.y, player_momentum.x)
        substeps = 5
        substep_dt = dt / substeps

        # loop to check for collisions multiple times per frame, to prevent tunneling at high speeds. More iterations means less tunneling but more CPU usage, so this is a balance.
        for _ in range(substeps):
            prev_pos = new_player_pos.copy()
            new_player_pos += player_momentum * substep_dt


            # Rectangle hitbox centered on the player position.
            rect = pygame.Rect(
                new_player_pos.x - player_radius,
                new_player_pos.y - player_radius,
                player_radius * 2,
                player_radius * 2,
            )
            prev_rect = pygame.Rect(
                prev_pos.x - player_radius,
                prev_pos.y - player_radius,
                player_radius * 2,
                player_radius * 2,
            )
            swept_rect = rect.union(prev_rect)

            colliding_lines = [line for line in boundries if swept_rect.clipline(*line[0], *line[1])]
            collision = len(colliding_lines) > 0
            
            if collision:
                hit_wall = True
                collision_normal = pygame.Vector2(0, 0)

                bounce_factor = 0.8
                bounce_factor_total = 0

                # Build a single average normal so corners don't double-reflect in one frame.
                for line in colliding_lines:
                    line_start = pygame.Vector2(line[0])
                    line_end = pygame.Vector2(line[1])
                    line_vec = line_end - line_start
                    if line_vec.length_squared() == 0:
                        continue

                    normal = pygame.Vector2(-line_vec.y, line_vec.x).normalize()
                    line_mid = (line_start + line_end) * 0.5


                    bounce_factor_total += bouncy_boundries[colliding_lines.index(line)]

                    # Flip normal so it points toward the player's current side of the line.
                    if normal.dot(new_player_pos - line_mid) < 0:
                        normal *= -1

                    collision_normal += normal

                bounce_factor = bounce_factor_total / len(colliding_lines) if len(colliding_lines) > 0 else 0.8
                if collision_normal.length_squared() == 0:
                    collision_normal = pygame.Vector2(0, -1)
                else:
                    collision_normal = collision_normal.normalize()


                if player_momentum.dot(collision_normal) < 0:
                    hit_wall = True
                    player_momentum.reflect_ip(collision_normal)
                    # change momentum based on bounce factor
                    player_momentum *= bounce_factor

                # Move out of penetration with a hard cap to avoid lock-ups.
                max_push_iterations = 200
                push_iterations = 0
                while any(rect.clipline(*line[0], *line[1]) for line in boundries) and push_iterations < max_push_iterations:
                    new_player_pos += collision_normal
                    rect = pygame.Rect(
                        new_player_pos.x - player_radius,
                        new_player_pos.y - player_radius,
                        player_radius * 2,
                        player_radius * 2,
                    )
                    push_iterations += 1
                        


    if is_charging:
        new_player_pos = player_pos  # Don't move while charging, but still check for wall collisions to prevent charging into a wall.

    if hit_wall and freeze_available:
        paused_until = current_ticks + hit_stun_ms
        freeze_available = False

    player_pos = new_player_pos
    player_angle = new_player_angle

    magnitude = math.sqrt(player_momentum.x ** 2 + player_momentum.y ** 2) + 20 * 100

    charge_magnitude = max(20, min((current_ticks - charge_start_ms) / max_charge_ms, 1) * 100) * 100
    
    if is_charging:
        draw_arrow(screen, player_pos, player_pos + pygame.Vector2(math.cos(direction), math.sin(direction)) * charge_magnitude / 100, "yellow", body_width=6, head_width=12, head_height=6)
    else:
        draw_arrow(screen, player_pos, player_pos + pygame.Vector2(math.cos(direction), math.sin(direction)) * magnitude / 100, "white", body_width=6, head_width=12, head_height=6)


    # ui.
    #cooldownbar
    pygame.draw.rect(screen, "black", (10, 10, 200, 20), 10, 5)
    bounce_recharge = min(1, (current_ticks - last_dash) / current_cooldown)
    pygame.draw.rect(screen,"green", (12,12,196*bounce_recharge,16), 0, 3)

    #speed
    font = pygame.font.SysFont(None, 24)
    if is_charging:
        speed_text = font.render(f"Charging: {int(charge_magnitude/100)}%", True, "white")
    else:
        speed_text = font.render(f"Speed: {int(math.sqrt(player_momentum.length()+4)/3)}", True, "white")
    screen.blit(speed_text, (10, 40))

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(frame_time) / 1000

pygame.quit()