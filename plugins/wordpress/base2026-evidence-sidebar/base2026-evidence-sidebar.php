<?php
/**
 * Plugin Name: Base2026 Evidence Sidebar
 * Description: Add a bounded, source-attributed public expert-video lookup to the block editor.
 * Version: 0.1.1
 * Requires at least: 6.5
 * Requires PHP: 7.4
 * Author: Base2026 contributors
 * License: GPLv2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: base2026-evidence-sidebar
 */

defined( 'ABSPATH' ) || exit;

/**
 * A deliberately small editor integration for Base2026's public evidence brief API.
 *
 * There are no settings, options, cookies, custom tables, telemetry hooks, or
 * background requests. The only outbound request is made after an editor
 * clicks Search and goes to the fixed public Base2026 endpoint below.
 */
final class Base2026_Evidence_Sidebar {
	const VERSION = '0.1.1';
	const REST_NAMESPACE = 'base2026/v1';
	const REST_ROUTE = '/search';
	const EVIDENCE_BRIEF_ENDPOINT = 'https://base2026.dev/api/evidence-brief/v2';
	const PRIVACY_URL = 'https://base2026.dev/privacy';
	const SERVICE_LIMITS_URL = 'https://base2026.dev/api';
	const SOURCE_POLICY_URL = 'https://base2026.dev/source-policy';
	const MAX_QUERY_CHARS = 160;
	const MAX_REQUEST_BODY_BYTES = 8192;
	const MAX_RESPONSE_BYTES = 262144;
	const MAX_RESULTS = 5;
	const REQUEST_TIMEOUT_SECONDS = 8;

	/**
	 * Register the plugin's two editor-only surfaces.
	 */
	public static function init() {
		add_action( 'rest_api_init', array( __CLASS__, 'register_rest_routes' ) );
		add_action( 'enqueue_block_editor_assets', array( __CLASS__, 'enqueue_editor_assets' ) );
	}

	/**
	 * Register a same-site route so the browser never needs a Base2026 key.
	 */
	public static function register_rest_routes() {
		register_rest_route(
			self::REST_NAMESPACE,
			self::REST_ROUTE,
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => array( __CLASS__, 'handle_search' ),
				'permission_callback' => array( __CLASS__, 'check_permissions' ),
				'args'                => array(
					'query' => array(
						'required'          => true,
						'type'              => 'string',
						'sanitize_callback' => static function ( $value ) {
							return is_string( $value ) ? trim( $value ) : $value;
						},
					),
				),
			)
		);
	}

	/**
	 * Require both the normal WP REST nonce and the editor capability.
	 *
	 * Base2026 itself remains a public no-key service; this local route is
	 * intentionally editor-authenticated so a random public visitor cannot use
	 * a WordPress installation as a proxy.
	 *
	 * @param WP_REST_Request $request Current REST request.
	 * @return true|WP_Error
	 */
	public static function check_permissions( $request ) {
		if ( ! current_user_can( 'edit_posts' ) ) {
			return new WP_Error(
				'base2026_editor_capability_required',
				__( 'You need permission to edit posts to use this editor search.', 'base2026-evidence-sidebar' ),
				array( 'status' => 403 )
			);
		}

		$nonce = $request->get_header( 'X-WP-Nonce' );
		if ( ! is_string( $nonce ) || '' === $nonce || ! wp_verify_nonce( $nonce, 'wp_rest' ) ) {
			return new WP_Error(
				'base2026_invalid_nonce',
				__( 'The editor security token is missing or expired. Reload the editor and try again.', 'base2026-evidence-sidebar' ),
				array( 'status' => 403 )
			);
		}

		return true;
	}

	/**
	 * Enqueue a plain, dependency-free Gutenberg sidebar script.
	 */
	public static function enqueue_editor_assets() {
		$handle = 'base2026-evidence-sidebar';
		wp_enqueue_script(
			$handle,
			plugins_url( 'assets/editor.js', __FILE__ ),
			array( 'wp-blocks', 'wp-components', 'wp-data', 'wp-edit-post', 'wp-element', 'wp-plugins' ),
			self::VERSION,
			true
		);

		$config = array(
			'restUrl'         => esc_url_raw( rest_url( self::REST_NAMESPACE . self::REST_ROUTE ) ),
			'nonce'           => wp_create_nonce( 'wp_rest' ),
			'privacyUrl'      => self::PRIVACY_URL,
			'serviceLimitsUrl' => self::SERVICE_LIMITS_URL,
			'sourcePolicyUrl' => self::SOURCE_POLICY_URL,
			'maxQueryChars'   => self::MAX_QUERY_CHARS,
		);

		wp_add_inline_script(
			$handle,
			'window.Base2026EvidenceSidebarConfig = ' . wp_json_encode(
				$config,
				JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT
			) . ';',
			'before'
		);
	}

	/**
	 * Validate the request and proxy only the fixed, bounded public evidence brief.
	 *
	 * @param WP_REST_Request $request Current REST request.
	 * @return WP_REST_Response|WP_Error
	 */
	public static function handle_search( $request ) {
		$body = $request->get_body();
		if ( ! is_string( $body ) || strlen( $body ) > self::MAX_REQUEST_BODY_BYTES ) {
			return self::error(
				'base2026_request_too_large',
				__( 'The search request is too large.', 'base2026-evidence-sidebar' ),
				413
			);
		}

		$params = $request->get_json_params();
		if ( ! is_array( $params ) ) {
			return self::error(
				'base2026_invalid_json',
				__( 'Send a JSON object containing one short query.', 'base2026-evidence-sidebar' ),
				400
			);
		}

		$keys = array_keys( $params );
		if ( 1 !== count( $keys ) || 'query' !== $keys[0] ) {
			return self::error(
				'base2026_unexpected_input',
				__( 'Only the query field is accepted.', 'base2026-evidence-sidebar' ),
				400
			);
		}

		$query = $params['query'];
		if ( ! is_string( $query ) ) {
			return self::error(
				'base2026_invalid_query',
				__( 'The query must be text.', 'base2026-evidence-sidebar' ),
				400
			);
		}

		$query = trim( $query );
		$query_length = function_exists( 'mb_strlen' ) ? mb_strlen( $query, 'UTF-8' ) : strlen( $query );
		if ( 0 === $query_length || $query_length > self::MAX_QUERY_CHARS ) {
			return self::error(
				'base2026_query_length',
				sprintf(
					/* translators: %d: maximum number of characters. */
					__( 'Use a short query between 1 and %d characters.', 'base2026-evidence-sidebar' ),
					self::MAX_QUERY_CHARS
				),
				400
			);
		}

		if ( 1 !== preg_match( '//u', $query ) || 1 === preg_match( '/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', $query ) ) {
			return self::error(
				'base2026_invalid_query',
				__( 'The query contains unsupported characters.', 'base2026-evidence-sidebar' ),
				400
			);
		}

		$upstream_url = add_query_arg( 'q', $query, self::EVIDENCE_BRIEF_ENDPOINT );
		$response = wp_safe_remote_get(
			$upstream_url,
			array(
				'user-agent'          => 'Base2026-Evidence-Sidebar/0.1.1',
				'timeout'             => self::REQUEST_TIMEOUT_SECONDS,
				'redirection'        => 0,
				'blocking'            => true,
				'httpversion'         => '1.1',
				'reject_unsafe_urls'  => true,
				'limit_response_size' => self::MAX_RESPONSE_BYTES,
				'headers'             => array(
					'Accept'       => 'application/json',
				),
			)
		);

		if ( is_wp_error( $response ) ) {
			return self::error(
				'base2026_upstream_unavailable',
				__( 'The public Base2026 evidence brief is temporarily unavailable. Try again shortly.', 'base2026-evidence-sidebar' ),
				502
			);
		}

		$status = (int) wp_remote_retrieve_response_code( $response );
		if ( 429 === $status ) {
			return self::error(
				'base2026_rate_limited',
				__( 'The public Base2026 evidence brief is rate-limited. Wait a moment before trying again.', 'base2026-evidence-sidebar' ),
				429
			);
		}
		if ( $status < 200 || $status >= 300 ) {
			return self::error(
				'base2026_upstream_http_error',
				__( 'The public Base2026 evidence brief returned an unavailable response. Try again shortly.', 'base2026-evidence-sidebar' ),
				502
			);
		}

		$decoded = json_decode( wp_remote_retrieve_body( $response ), true );
		if ( JSON_ERROR_NONE !== json_last_error() || ! is_array( $decoded ) || ! isset( $decoded['findings'] ) || ! is_array( $decoded['findings'] ) ) {
			return self::error(
				'base2026_invalid_upstream_response',
				__( 'The public Base2026 evidence brief returned an unreadable response. Try again shortly.', 'base2026-evidence-sidebar' ),
				502
			);
		}

		$cards = self::normalize_cards( $decoded['findings'] );
		if ( is_wp_error( $cards ) ) {
			return $cards;
		}

		return rest_ensure_response(
			array(
				'results' => $cards,
			)
		);
	}

	/**
	 * Convert only short public card fields into the WordPress response.
	 *
	 * Full transcript fields, internal identifiers, rankings and upstream
	 * metadata are intentionally not forwarded to the editor.
	 *
	 * @param array $findings Evidence Brief v2 findings.
	 * @return array|WP_Error
	 */
	private static function normalize_cards( $findings ) {
		$cards      = array();
		$seen       = array();
		$hit_count  = 0;
		$valid_count = 0;

		foreach ( $findings as $finding ) {
			$hit_count++;
			if ( ! is_array( $finding ) ) {
				continue;
			}

			$title   = self::clean_text( isset( $finding['claim'] ) ? $finding['claim'] : '', 180 );
			$excerpt = self::clean_text( isset( $finding['evidence_excerpt'] ) ? $finding['evidence_excerpt'] : '', 480 );
			if ( '' === $title && '' === $excerpt ) {
				continue;
			}
			if ( '' === $title ) {
				$title = __( 'Source excerpt', 'base2026-evidence-sidebar' );
			}

			$original_url = self::safe_url( isset( $finding['original_source_url'] ) ? $finding['original_source_url'] : '' );
			$base2026_url = self::safe_base2026_url( isset( $finding['base2026_url'] ) ? $finding['base2026_url'] : '' );
			$identity      = $base2026_url . '|' . $original_url . '|' . $title;
			if ( isset( $seen[ $identity ] ) ) {
				continue;
			}
			$seen[ $identity ] = true;

			$cards[] = array(
				'title'               => $title,
				'title_kind'          => 'source_claim_label',
				'excerpt'             => $excerpt,
				'excerpt_kind'        => '' !== $excerpt ? 'public_evidence_excerpt' : 'source_claim_only',
				'provenance'          => 'Base2026 Evidence Brief v2 · public source finding',
				'creator'             => self::clean_text( isset( $finding['creator_handle'] ) ? $finding['creator_handle'] : '', 120 ),
				'published'           => self::clean_text( isset( $finding['published_date'] ) ? $finding['published_date'] : '', 30 ),
				'original_url'        => $original_url,
				'base2026_url'        => $base2026_url,
				'source_quality_note' => __( 'This card shows what an attributed public source says. It is not independent verification, a consensus score, or a promise that the recommendation works.', 'base2026-evidence-sidebar' ),
			);
			$valid_count++;
			if ( count( $cards ) >= self::MAX_RESULTS ) {
				break;
			}
		}

		if ( $hit_count > 0 && 0 === $valid_count ) {
			return self::error(
				'base2026_unusable_upstream_schema',
				__( 'The public Base2026 evidence brief returned no usable source cards. Try again shortly.', 'base2026-evidence-sidebar' ),
				502
			);
		}

		return $cards;
	}

	/**
	 * Accept a documented Base2026 source page only from a validated host/path.
	 *
	 * @param mixed $value Candidate Base2026 URL.
	 * @return string
	 */
	private static function safe_base2026_url( $value ) {
		$url = self::safe_url( $value );
		if ( '' === $url ) {
			return '';
		}

		$parts = wp_parse_url( $url );
		if ( ! is_array( $parts ) || 'base2026.dev' !== strtolower( isset( $parts['host'] ) ? $parts['host'] : '' ) || empty( $parts['path'] ) || 0 !== strpos( $parts['path'], '/sources/' ) ) {
			return '';
		}

		return $url;
	}

	/**
	 * Strip markup and bound public text before it leaves the server.
	 *
	 * @param mixed $value Value from the public response.
	 * @param int   $limit Maximum characters.
	 * @return string
	 */
	private static function clean_text( $value, $limit ) {
		if ( ! is_string( $value ) ) {
			return '';
		}

		$value = html_entity_decode( wp_strip_all_tags( $value ), ENT_QUOTES | ENT_HTML5, 'UTF-8' );
		$value = preg_replace( '/\s+/u', ' ', $value );
		$value = is_string( $value ) ? trim( $value ) : '';
		if ( '' === $value ) {
			return '';
		}

		if ( function_exists( 'mb_substr' ) ) {
			return mb_substr( $value, 0, $limit, 'UTF-8' );
		}
		return substr( $value, 0, $limit );
	}

	/**
	 * Accept public source links only when they are absolute HTTP(S) URLs.
	 *
	 * @param mixed $value Candidate URL.
	 * @return string
	 */
	private static function safe_url( $value ) {
		if ( ! is_string( $value ) || '' === trim( $value ) ) {
			return '';
		}

		$parts = wp_parse_url( trim( $value ) );
		if ( ! is_array( $parts ) || empty( $parts['scheme'] ) || empty( $parts['host'] ) ) {
			return '';
		}
		if ( ! in_array( strtolower( $parts['scheme'] ), array( 'http', 'https' ), true ) ) {
			return '';
		}
		if ( isset( $parts['user'] ) || isset( $parts['pass'] ) ) {
			return '';
		}

		return esc_url_raw( trim( $value ), array( 'http', 'https' ) );
	}

	/**
	 * Return a REST error with a bounded status code.
	 *
	 * @param string $code Error code.
	 * @param string $message User-facing message.
	 * @param int    $status HTTP status.
	 * @return WP_Error
	 */
	private static function error( $code, $message, $status ) {
		return new WP_Error( $code, $message, array( 'status' => $status ) );
	}
}

Base2026_Evidence_Sidebar::init();
