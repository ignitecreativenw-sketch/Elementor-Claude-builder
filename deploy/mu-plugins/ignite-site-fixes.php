<?php
/**
 * Plugin Name:  Ignite site fixes (per-site copy)
 * Description:  Accessibility, SEO and performance fixes that cannot be made
 *               from Elementor or the REST API. Drop-in must-use plugin.
 * Version:      1.2.0
 * Author:       Ignite Creative
 *
 * WHY A MU-PLUGIN AND NOT A CHILD THEME
 * -------------------------------------
 * The three things that need fixing here are not theme design decisions — they
 * are behaviours of Elementor's page template, of Yoast's REST registration and
 * of the document head. A child theme would fix the first by copying Hello
 * Elementor's header-footer template wholesale, which then silently goes stale
 * every time the theme updates. Hooks do the same job in a dozen lines and keep
 * working. A must-use plugin also cannot be deactivated by accident, and it
 * survives a theme switch, which matters on a site that is still being built.
 *
 * INSTALL
 * -------
 * Upload this file to:   wp-content/mu-plugins/ignite-site-fixes.php
 * Create the mu-plugins directory if it does not exist. No activation step —
 * must-use plugins load automatically. To remove it, delete the file.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* ---------------------------------------------------------------------------
 * 1. The <main> landmark, and a skip link that works
 *
 * PageSpeed: accessibility "landmark-one-main" and "skip-link" both fail.
 * Elementor's header-footer page template prints the page content with no
 * <main> wrapper, so assistive tech has no main landmark to jump to — and
 * Hello Elementor's skip link points at #content, which does not exist.
 *
 * One <main id="content"> fixes both. These two hooks fire either side of the
 * content in Elementor's header-footer template, which is the template every
 * page on this site uses.
 * ------------------------------------------------------------------------- */
add_action( 'elementor/page_templates/header-footer/before_content', function () {
	echo '<main id="content" class="site-main" role="main">';
}, 5 );

add_action( 'elementor/page_templates/header-footer/after_content', function () {
	echo '</main>';
}, 50 );

/**
 * Hello Elementor hides the skip link with .screen-reader-text, which clips it
 * out of the viewport. Lighthouse reports it as "not focusable" because the
 * theme's focus rule does not always win. This brings it back on focus.
 */
add_action( 'wp_head', function () {
	echo '<style id="teb-skip-link">'
		. '.skip-link.screen-reader-text:focus{'
		. 'position:fixed!important;top:8px!important;left:8px!important;'
		. 'width:auto!important;height:auto!important;clip:auto!important;'
		. 'clip-path:none!important;overflow:visible!important;'
		. 'z-index:100000;padding:12px 20px;border-radius:8px;'
		. 'background:#FFFFFF;color:#053480;/* PER SITE: brand colour + heading font */font:600 15px/1.2 Montserrat,sans-serif;'
		. 'text-decoration:none;box-shadow:0 4px 18px rgba(4,16,58,.25);'
		. 'outline:3px solid #053480;outline-offset:2px;}'
		. '</style>';
}, 1 );

/* ---------------------------------------------------------------------------
 * 2. Yoast's meta description, writable over the REST API
 *
 * Yoast stores the description in _yoast_wpseo_metadesc but does not register
 * it for REST, so a write through /wp/v2/pages/<id> is silently dropped. This
 * registers the two fields we populate from the build, with an edit-posts
 * capability check so it is no more permissive than the admin screen.
 *
 * Yoast keeps reading the same meta keys, so anything written here shows up in
 * its sidebar exactly as if it had been typed there.
 * ------------------------------------------------------------------------- */
add_action( 'init', function () {
	$types = array( 'page', 'post' );
	$keys  = array( '_yoast_wpseo_metadesc', '_yoast_wpseo_title' );

	foreach ( $types as $type ) {
		foreach ( $keys as $key ) {
			register_post_meta( $type, $key, array(
				'type'          => 'string',
				'single'        => true,
				'show_in_rest'  => true,
				'auth_callback' => function ( $allowed, $meta_key, $post_id ) {
					return current_user_can( 'edit_post', $post_id );
				},
			) );
		}
	}
}, 20 );

/* ---------------------------------------------------------------------------
 * 3. Preload the hero image
 *
 * PageSpeed: "LCP request discovery". The hero is a CSS background, so the
 * browser cannot find it until the stylesheet has parsed — it is the last
 * thing discovered and the largest thing painted. A preload hint in the head
 * starts the download immediately.
 *
 * Two files, because a CSS background gets no srcset: the mobile crop and the
 * full-size one, picked apart by a media query so a phone never fetches both.
 * Only on the front page, which is the only place this hero appears.
 * ------------------------------------------------------------------------- */
add_action( 'wp_head', function () {
	if ( ! is_front_page() ) {
		return;
	}

	$uploads = wp_get_upload_dir();
	$base    = trailingslashit( $uploads['baseurl'] ) . '2026/09/';

	$variants = array(
		'hero-london-skyline-m.webp' => '(max-width: 767px)',
		'hero-london-skyline.webp'   => '(min-width: 768px)',
	);

	foreach ( $variants as $file => $media ) {
		printf(
			'<link rel="preload" as="image" href="%s" media="%s" fetchpriority="high">',
			esc_url( $base . $file ),
			esc_attr( $media )
		);
	}
}, 2 );

/* ---------------------------------------------------------------------------
 * 4. Google Fonts off the critical path
 *
 * PageSpeed, mobile: render-blocking requests total 2,050ms, and Google Fonts
 * is 2,400ms of the blocking duration for 7 KiB across THREE separate
 * /css?family= requests. It is the single most expensive thing in the critical
 * path by time, and the cheapest by bytes.
 *
 * The media="print" / onload swap loads the stylesheet asynchronously: the
 * browser fetches it at low priority and does not block the first paint on it.
 * Elementor already sets font-display:swap, so text paints immediately in the
 * fallback and swaps to Montserrat when it lands — no invisible text, and no
 * layout shift beyond the glyph swap (CLS is currently 0.007, with headroom).
 *
 * A <noscript> copy keeps the font for anyone without JavaScript.
 *
 * Before any of that, families the design does not use are dropped. See
 * teb_font_families_in_use() below — on this site that removes two of the
 * three requests outright.
 * ------------------------------------------------------------------------- */
/**
 * Fonts the design actually uses. Elementor's default kit asks for Roboto and
 * Roboto Slab as well, which is TWO of the THREE blocking font requests on
 * this site — roughly 1,500ms of the 2,400ms — for typefaces that appear
 * nowhere in the build. Everything here is Montserrat.
 *
 * Anything not on this list is dropped outright rather than deferred.
 */
function teb_font_families_in_use() {
	return apply_filters( 'teb_font_families_in_use', array( 'Montserrat' ) /* PER SITE: the families the build actually uses */ );
}

add_filter( 'style_loader_tag', function ( $tag, $handle, $href ) {
	if ( is_admin() || strpos( $href, 'fonts.googleapis.com' ) === false ) {
		return $tag;
	}

	// Drop font families the design never uses.
	$wanted = false;
	foreach ( teb_font_families_in_use() as $family ) {
		if ( stripos( $href, str_replace( ' ', '+', $family ) ) !== false ) {
			$wanted = true;
			break;
		}
	}
	if ( ! $wanted ) {
		return '';
	}

	$async = str_replace(
		"media='all'",
		"media='print' onload=\"this.media='all';this.onload=null;\"",
		$tag
	);

	// str_replace above only fires when WordPress used single quotes; cover
	// the double-quoted form too rather than assuming either.
	if ( $async === $tag ) {
		$async = str_replace(
			'media="all"',
			'media="print" onload="this.media=\'all\';this.onload=null;"',
			$tag
		);
	}

	return $async . sprintf( '<noscript>%s</noscript>', $tag );
}, 10, 3 );

/**
 * Warm the font connection while the HTML is still parsing, so the async
 * request above does not pay for DNS and TLS when it finally fires.
 */
add_action( 'wp_head', function () {
	echo '<link rel="preconnect" href="https://fonts.googleapis.com">'
		. '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>';
}, 1 );

/* ---------------------------------------------------------------------------
 * 5. Drop jquery-migrate
 *
 * 4.8 KiB and 330ms in the render-blocking list. It is a compatibility shim
 * for jQuery 1.x-era code; nothing on this site needs it. Front end only —
 * the admin keeps it, because plugin screens sometimes do rely on it.
 * ------------------------------------------------------------------------- */
add_action( 'wp_default_scripts', function ( $scripts ) {
	if ( is_admin() || empty( $scripts->registered['jquery'] ) ) {
		return;
	}
	$scripts->registered['jquery']->deps = array_diff(
		$scripts->registered['jquery']->deps,
		array( 'jquery-migrate' )
	);
} );

/* ---------------------------------------------------------------------------
 * 6. Cache headers for static assets  —  NOT FIXABLE FROM HERE
 *
 * PageSpeed: "use efficient cache lifetimes", 313 KiB, every first-party
 * asset reporting Cache TTL: None.
 *
 * An earlier version of this file carried an .htaccess block for mod_expires.
 * That advice was wrong for this server. Checked from a real browser on the
 * live site:
 *
 *   server: nginx
 *   cache-control: (absent)
 *   expires: (absent)
 *
 * nginx does not read .htaccess, and it serves /wp-content/uploads and
 * /wp-includes directly without going through PHP — so neither an .htaccess
 * rule nor a WordPress filter can set these headers. There is nothing this
 * plugin can do about it.
 *
 * It has to be set where the files are actually served:
 *
 *   - the host control panel's static / browser caching setting (20i StackCP
 *     exposes this per site), or
 *   - the CDN in front of it — the edge layer is already stamping
 *     cf-edge-cache headers on responses, so a Browser Cache TTL of 1 year
 *     there would cover it, or
 *   - an nginx location block, if there is access to the vhost config:
 *
 *       location ~* \.(webp|png|jpe?g|svg|css|js|woff2)$ {
 *           expires 1y;
 *           add_header Cache-Control "public, immutable";
 *       }
 *
 * WordPress and Elementor both version their asset URLs, so a year is safe.
 * ------------------------------------------------------------------------- */
