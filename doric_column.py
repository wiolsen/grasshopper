import rhinoscriptsyntax as rs
import math

def create_doric_column():
    # 1. Get User Parameters
    height = rs.GetReal("Column Height", 10.0)
    if height is None: return
    
    base_radius = rs.GetReal("Base Radius", 1.0)
    if base_radius is None: return
    
    top_radius = rs.GetReal("Top Radius", 0.8)
    if top_radius is None: return
    
    flute_count = rs.GetInteger("Number of Flutes", 20)
    if flute_count is None: return
    
    # Disable redraw for speed
    rs.EnableRedraw(False)
    
    # 2. Create the Shaft (Truncated Cone)
    # Base plane is WorldXY
    # plane = rs.WorldXYPlane()
    # AddTruncatedCone(plane, height, radius1, radius2, cap=True)
    rs.Command("_-TruncatedCone 0,0,0 " + str(base_radius) + " 0,0," + str(height) + " " + str(top_radius))
    shaft = rs.LastCreatedObjects()[0]
    
    # 3. Create Flutes (Boolean Subtraction)
    cutters = []
    
    # Calculate flute dimensions
    # We want the flutes to be roughly semi-circular or shallow arcs.
    # We calculate the chord length between flute centers on the surface.
    
    for i in range(flute_count):
        angle = (2 * math.pi / flute_count) * i
        
        # Calculate start and end points for the flute axis (following the taper)
        # We place the center of the cutter pipe exactly on the surface of the column
        
        # Bottom point
        x1 = base_radius * math.cos(angle)
        y1 = base_radius * math.sin(angle)
        z1 = 0
        
        # Top point
        x2 = top_radius * math.cos(angle)
        y2 = top_radius * math.sin(angle)
        z2 = height
        
        # Calculate appropriate radius for the cutter pipe
        # Chord length at bottom
        chord_bottom = 2 * base_radius * math.sin(math.pi / flute_count)
        # Use slightly more than half chord for a reasonably deep flute, 
        # or exactly half for semi-circle if flat.
        # For Doric, we want sharp arrises (ridges), so the cuts must meet.
        # If radius = chord/2 and centered on chord, they meet.
        # If centered on surface (arc), we need to adjust.
        # Let's use a factor.
        flute_radius_bottom = chord_bottom * 0.5
        
        # Chord length at top
        chord_top = 2 * top_radius * math.sin(math.pi / flute_count)
        flute_radius_top = chord_top * 0.5
        
        # Extend the cutter axis to avoid coincident faces at top and bottom
        p1 = rs.coerce3dpoint([x1, y1, z1])
        p2 = rs.coerce3dpoint([x2, y2, z2])
        vector = p2 - p1
        length = vector.Length
        unit_vector = vector / length
        
        extension = length * 0.1 # Extend by 10%
        
        p1_ext = p1 - unit_vector * extension
        p2_ext = p2 + unit_vector * extension
        
        # Adjust radii for the extended pipe
        radius_slope = (flute_radius_top - flute_radius_bottom) / length
        r1_ext = flute_radius_bottom - radius_slope * extension
        r2_ext = flute_radius_top + radius_slope * extension
        
        # Create the axis line for the pipe
        line = rs.AddLine(p1_ext, p2_ext)
        
        # Create the tapered pipe cutter
        # params=[0,1] (start, end), radii=[r_bot, r_top], cap=1 (flat)
        domain = rs.CurveDomain(line)
        cutter = rs.AddPipe(line, [domain[0], domain[1]], [r1_ext, r2_ext], 1, 1)
        
        rs.DeleteObject(line)
        if cutter:
            cutters.append(cutter)
        
    # Perform Boolean Difference
    if cutters:
        # rs.BooleanDifference(input_0, input_1, delete_input=True)
        # input_0: object to subtract from
        # input_1: objects to subtract
        diff_result = rs.BooleanDifference([shaft], cutters)
        if diff_result:
            shaft = diff_result[0] # Update shaft ID to the new object
        else:
            # Fallback if boolean fails (e.g. geometry issues), clean up cutters
            rs.DeleteObjects(cutters)

    # 4. Create Capital
    # The capital consists of the Echinus (cushion) and Abacus (flat slab).
    
    # Echinus parameters
    echinus_height = top_radius * 0.5
    echinus_base_r = top_radius
    echinus_top_r = top_radius * 1.5
    
    # base_plane = rs.WorldXYPlane()
    # echinus_origin = rs.PointAdd(base_plane[0], rs.VectorScale(base_plane[3], height))
    # echinus_plane = rs.PlaneFromFrame(echinus_origin, base_plane[1], base_plane[2])
    
    rs.Command("_-TruncatedCone 0,0," + str(height) + " " + str(echinus_base_r) + " 0,0," + str(height + echinus_height) + " " + str(echinus_top_r))
    echinus = rs.LastCreatedObjects()[0]
    
    # Abacus parameters
    abacus_width = echinus_top_r * 1.4 # Square width
    abacus_height = top_radius * 0.4
    abacus_z = height + echinus_height
    
    # Create Abacus Box
    # Corners
    half_w = abacus_width / 2.0
    p0 = [-half_w, -half_w, abacus_z]
    p1 = [half_w, -half_w, abacus_z]
    p2 = [half_w, half_w, abacus_z]
    p3 = [-half_w, half_w, abacus_z]
    p4 = [-half_w, -half_w, abacus_z + abacus_height]
    p5 = [half_w, -half_w, abacus_z + abacus_height]
    p6 = [half_w, half_w, abacus_z + abacus_height]
    p7 = [-half_w, half_w, abacus_z + abacus_height]
    
    abacus = rs.AddBox([p0, p1, p2, p3, p4, p5, p6, p7])
    
    # 5. Combine all parts
    # Union Echinus and Abacus first
    capital = rs.BooleanUnion([echinus, abacus])
    if capital:
        capital = capital[0]
        # Union Shaft and Capital
        final_column = rs.BooleanUnion([shaft, capital])
        if final_column:
            rs.SelectObject(final_column[0])
    
    rs.EnableRedraw(True)
    print("Doric column generated.")

if __name__ == "__main__":
    create_doric_column()
